import os
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.services.source_storage import safe_extract_tar, safe_extract_zip
from app.utils.config import DEFAULT_BUILD_CONTEXT_BASE_DIR



def build_context_root(user_id: int, image_id: int) -> str:
    
    return str(Path(DEFAULT_BUILD_CONTEXT_BASE_DIR) / str(user_id) / str(image_id))


def save_upload_to_disk(file: UploadFile, dest_path: str) -> None:
    if file.file is None:
        raise HTTPException(status_code=400, detail="Missing file content")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)


def extract_archive(filename: str, archive_path: str, context_dir: str) -> None:
    name = (filename or "").lower()
    if name.endswith((".tar", ".tar.gz", ".tgz")):
        safe_extract_tar(archive_path, context_dir)
        return
    if name.endswith(".zip"):
        safe_extract_zip(archive_path, context_dir)
        return
    raise HTTPException(status_code=400, detail="Unsupported file type. Use .zip or .tar.gz")


def validate_context(context_dir: str) -> None:
    dockerfile_path = Path(context_dir) / "Dockerfile"
    if not dockerfile_path.exists() or not dockerfile_path.is_file():
        raise HTTPException(status_code=400, detail="Dockerfile not found at context root")


def prepare_context(user_id: int, image_id: int, file: UploadFile) -> tuple[str, str]:
    root_dir = Path(build_context_root(user_id, image_id))
    root_dir.mkdir(parents=True, exist_ok=True)

    archive_path = root_dir / f"upload-{uuid.uuid4().hex}"
    save_upload_to_disk(file, str(archive_path))

    context_dir = root_dir / "context"
    if context_dir.exists():
        shutil.rmtree(context_dir)
    context_dir.mkdir(parents=True, exist_ok=True)

    extract_archive(file.filename or "", str(archive_path), str(context_dir))
    validate_context(str(context_dir))

    try:
        archive_path.unlink(missing_ok=True)
    except Exception:
        pass

    return str(root_dir), str(context_dir)


def cleanup_context(root_dir: str) -> None:
    if not root_dir:
        return
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir, ignore_errors=True)