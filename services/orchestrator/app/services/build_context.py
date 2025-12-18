import os
import shutil
import uuid
import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.services.source_storage import safe_extract_tar, safe_extract_zip
from app.utils.config import DEFAULT_BUILD_CONTEXT_BASE_DIR

logger = logging.getLogger("orchestrator")



def build_context_root(user_id: int, image_id: int) -> str:
    
    return str(Path(DEFAULT_BUILD_CONTEXT_BASE_DIR) / str(user_id) / str(image_id))


async def save_upload_to_disk(file: UploadFile, dest_path: str) -> None:
    """Save uploaded file to disk.
    
    Args:
        file: FastAPI UploadFile object
        dest_path: Destination path where file will be saved
    
    Raises:
        HTTPException: If file cannot be saved
    """
    logger.info(
        "build_context.save_upload.start",
        extra={
            "dest_path": dest_path,
            "upload_file": file.filename,
            "content_type": file.content_type,
        }
    )
    
    try:
        # Read the file content as bytes
        content = await file.read()
        file_size = len(content)
        
        logger.info(
            "build_context.save_upload.read_complete",
            extra={
                "upload_file": file.filename,
                "size_bytes": file_size,
            }
        )
        
        # Write to disk
        with open(dest_path, "wb") as f:
            f.write(content)
        
        logger.info(
            "build_context.save_upload.success",
            extra={
                "dest_path": dest_path,
                "size_bytes": file_size,
            }
        )
    except Exception as e:
        logger.error(
            "build_context.save_upload.failed",
            extra={
                "dest_path": dest_path,
                "upload_file": file.filename,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        ) from e


def extract_archive(filename: str, archive_path: str, context_dir: str) -> None:
    """Extract archive to context directory.
    
    Args:
        filename: Original filename to determine archive type
        archive_path: Path to archive file
        context_dir: Destination directory for extraction
    
    Raises:
        HTTPException: If archive type is unsupported or extraction fails
    """
    name = (filename or "").lower()
    
    logger.info(
        "build_context.extract.start",
        extra={
            "archive_file": filename,
            "archive_path": archive_path,
            "context_dir": context_dir,
        }
    )
    
    try:
        if name.endswith((".tar", ".tar.gz", ".tgz")):
            safe_extract_tar(archive_path, context_dir)
            logger.info("build_context.extract.success", extra={"type": "tar"})
            return
        if name.endswith(".zip"):
            safe_extract_zip(archive_path, context_dir)
            logger.info("build_context.extract.success", extra={"type": "zip"})
            return
        
        logger.warning(
            "build_context.extract.unsupported_type",
            extra={"archive_file": filename}
        )
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use .zip or .tar.gz"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "build_context.extract.failed",
            extra={
                "archive_file": filename,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract archive: {str(e)}"
        ) from e


def validate_context(context_dir: str) -> None:
    """Validate that build context contains a Dockerfile.
    
    Args:
        context_dir: Path to build context directory
    
    Raises:
        HTTPException: If Dockerfile is not found
    """
    dockerfile_path = Path(context_dir) / "Dockerfile"
    
    if not dockerfile_path.exists() or not dockerfile_path.is_file():
        logger.error(
            "build_context.validate.no_dockerfile",
            extra={"context_dir": context_dir}
        )
        raise HTTPException(
            status_code=400,
            detail="Dockerfile not found at context root"
        )
    
    logger.debug(
        "build_context.validate.success",
        extra={"context_dir": context_dir}
    )


async def prepare_context(user_id: int, image_id: int, file: UploadFile) -> tuple[str, str]:
    """Prepare build context from uploaded archive.
    
    Saves uploaded file, extracts it, validates it contains a Dockerfile,
    and returns paths to root and context directories.
    
    Args:
        user_id: User ID for organizing build contexts
        image_id: Image ID for organizing build contexts
        file: Uploaded archive file (tar.gz or zip)
    
    Returns:
        Tuple of (root_dir, context_dir) paths
    
    Raises:
        HTTPException: If any step of preparation fails
    """
    logger.info(
        "build_context.prepare.start",
        extra={
            "user_id": user_id,
            "image_id": image_id,
            "upload_file": file.filename,
        }
    )
    
    # Create root directory for this image
    root_dir = Path(build_context_root(user_id, image_id))
    root_dir.mkdir(parents=True, exist_ok=True)
    
    logger.debug(
        "build_context.prepare.root_created",
        extra={"root_dir": str(root_dir)}
    )

    # Save uploaded file
    archive_path = root_dir / f"upload-{uuid.uuid4().hex}"
    await save_upload_to_disk(file, str(archive_path))

    # Prepare context directory
    context_dir = root_dir / "context"
    if context_dir.exists():
        logger.debug(
            "build_context.prepare.cleaning_old_context",
            extra={"context_dir": str(context_dir)}
        )
        shutil.rmtree(context_dir)
    context_dir.mkdir(parents=True, exist_ok=True)

    # Extract and validate
    extract_archive(file.filename or "", str(archive_path), str(context_dir))
    validate_context(str(context_dir))

    # Cleanup archive file
    try:
        archive_path.unlink(missing_ok=True)
        logger.debug("build_context.prepare.archive_cleaned")
    except Exception as e:
        logger.warning(
            "build_context.prepare.cleanup_failed",
            extra={"error": str(e)}
        )

    logger.info(
        "build_context.prepare.success",
        extra={
            "user_id": user_id,
            "image_id": image_id,
            "root_dir": str(root_dir),
            "context_dir": str(context_dir),
        }
    )

    return str(root_dir), str(context_dir)


def cleanup_context(root_dir: str) -> None:
    """Clean up build context directory.
    
    Args:
        root_dir: Root directory to remove
    """
    if not root_dir:
        return
    
    if os.path.exists(root_dir):
        logger.info(
            "build_context.cleanup.start",
            extra={"root_dir": root_dir}
        )
        try:
            shutil.rmtree(root_dir, ignore_errors=False)
            logger.info(
                "build_context.cleanup.success",
                extra={"root_dir": root_dir}
            )
        except Exception as e:
            logger.warning(
                "build_context.cleanup.failed",
                extra={
                    "root_dir": root_dir,
                    "error": str(e),
                },
                exc_info=True
            )