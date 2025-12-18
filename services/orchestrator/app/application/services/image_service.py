import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from app.schemas.image import ImageCreate
from app.database.models import Image, ContainerStatus
from app.repositories import images_repository, containers_repository
from app.services.build_context import prepare_context
from app.services import docker_service

logger = logging.getLogger("orchestrator")
MAX_STORED_BUILD_LOG_CHARS = 8000

def _assert_app_hostname_unique(db: Session, *, app_hostname: str, user_id: int) -> None:
    existing = images_repository.get_by_app_hostname(db, app_hostname=app_hostname, user_id=user_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Image with app_hostname '{app_hostname}' already exists for this user",
        )


def _create_image_row_and_flush(db: Session, *, data: ImageCreate) -> Image:
    image = Image(
        name=data.name,
        tag=data.tag,
        app_hostname=data.app_hostname,
        container_port=data.container_port,
        min_instances=data.min_instances,
        max_instances=data.max_instances,
        cpu_limit=data.cpu_limit,
        memory_limit=data.memory_limit,
        user_id=data.user_id,
        status="building",
    )
    images_repository.create(db, image)
    db.flush()
    return image


def _mark_failed_and_commit(db: Session, image: Image, *, build_logs: str | None = None) -> None:
    image.status = "build_failed"
    if build_logs is not None:
        image.build_logs = build_logs[-MAX_STORED_BUILD_LOG_CHARS:]
    db.commit()


def _mark_ready_and_commit(db: Session, image: Image) -> None:
    image.status = "ready"
    db.commit()


async def create_image_from_upload(
    *,
    db: Session,
    data: ImageCreate,
    file: UploadFile,
) -> Image:
    """Create an image from uploaded build context.
    
    This function orchestrates the complete image creation workflow:
    1. Validates app_hostname uniqueness
    2. Creates DB record with 'building' status
    3. Prepares build context from uploaded archive
    4. Builds Docker image
    5. Updates DB record with build logs and 'ready' status
    
    Args:
        db: Database session
        data: Image creation data (name, tag, app_hostname, etc.)
        file: Uploaded archive file containing Dockerfile and build context
    
    Returns:
        Created Image object with 'ready' or 'build_failed' status
    
    Raises:
        HTTPException: If creation fails at any step
    """
    db_image: Image | None = None
    build_logs: str | None = None
    
    logger.info(
        "image.create.start",
        extra={
            "app_hostname": data.app_hostname,
            "image_name": data.name,
            "image_tag": data.tag,
            "user_id": data.user_id,
            "upload_filename": file.filename,
        }
    )
    
    try:
        # Step 1: Validate uniqueness
        _assert_app_hostname_unique(db, app_hostname=data.app_hostname, user_id=data.user_id)
        
        # Step 2: Create DB record
        db_image = _create_image_row_and_flush(db, data=data)
        logger.info(
            "image.create.db_record_created",
            extra={
                "image_id": db_image.id,
                "app_hostname": data.app_hostname,
                "user_id": data.user_id,
            }
        )

        # Step 3: Prepare build context
        repo = f"nvidia-app-u{db_image.user_id}-i{db_image.id}"
        _, context_dir = await prepare_context(db_image.user_id, db_image.id, file)
        db_image.source_path = context_dir
        
        logger.info(
            "image.create.context_prepared",
            extra={
                "image_id": db_image.id,
                "context_dir": context_dir,
                "repository": repo,
            }
        )

        # Step 4: Build Docker image
        logger.info(
            "image.create.build_starting",
            extra={
                "image_id": db_image.id,
                "repository": repo,
                "image_tag": db_image.tag,
            }
        )
        
        build_logs = docker_service.build_image_from_context(context_dir, repo, db_image.tag)
        db_image.build_logs = build_logs[-MAX_STORED_BUILD_LOG_CHARS:]
        
        logger.info(
            "image.create.build_completed",
            extra={
                "image_id": db_image.id,
                "repository": repo,
                "image_tag": db_image.tag,
                "log_size": len(build_logs) if build_logs else 0,
            }
        )

        # Step 5: Mark as ready
        _mark_ready_and_commit(db, db_image)
        db.refresh(db_image)
        
        logger.info(
            "image.create.success",
            extra={
                "image_id": db_image.id,
                "app_hostname": data.app_hostname,
                "repository": repo,
                "image_tag": db_image.tag,
                "user_id": data.user_id,
            }
        )
        
        return db_image

    except HTTPException as e:
        logger.warning(
            "image.create.http_exception",
            extra={
                "error": str(e.detail),
                "status_code": e.status_code,
                "app_hostname": data.app_hostname,
                "user_id": data.user_id,
                "image_id": db_image.id if db_image else None,
            }
        )
        
        if db_image is not None and db_image.id is not None:
            try:
                detail_text = str(getattr(e, "detail", "")) if getattr(e, "detail", None) is not None else None
                _mark_failed_and_commit(db, db_image, build_logs=detail_text or build_logs)
            except Exception:
                db.rollback()
        else:
            db.rollback()
        raise e

    except Exception as e:
        logger.error(
            "image.create.failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "app_hostname": data.app_hostname,
                "user_id": data.user_id,
                "image_id": db_image.id if db_image else None,
            },
            exc_info=True
        )
        
        if db_image is not None and db_image.id is not None:
            try:
                _mark_failed_and_commit(db, db_image, build_logs=str(e))
            except Exception:
                db.rollback()
        else:
            db.rollback()
            
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create image: {str(e)}"
        ) from e

def get_all_images(db: Session, user_id: int):
    return images_repository.get_all_images(db, user_id)

def get_all_images_with_containers(db: Session, user_id: int):
    return images_repository.get_all_images_with_containers(db, user_id)

def get_image_by_id(db: Session, image_id: int, user_id: int) -> Image:
    """
    Get an image by ID, ensuring it belongs to the user.
    
    Args:
        db: Database session
        image_id: ID of the image to retrieve
        user_id: ID of the user (for access control)
    
    Returns:
        Image object
    
    Raises:
        HTTPException: 404 if image not found or doesn't belong to user
    """
    image = images_repository.get_by_id(db, image_id, user_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail=f"Image with id {image_id} not found or access denied"
        )

    return image


def delete_image(db: Session, image_id: int, user_id: int):
    """
    Delete an image if it has no running containers.
    
    Args:
        db: Database session
        image_id: ID of the image to delete
        user_id: ID of the user (for access control)
    
    Raises:
        HTTPException: 404 if image not found, 400 if image has running containers
    """
    logger.info(
        "image.delete.start",
        extra={
            "image_id": image_id,
            "user_id": user_id,
        }
    )
    
    image = get_image_by_id(db, image_id, user_id)
    
    containers = containers_repository.get_containers_by_image_id(db, image_id)
    
    running_containers = [c for c in containers if c.status == ContainerStatus.RUNNING]
    if running_containers:
        logger.warning(
            "image.delete.has_running_containers",
            extra={
                "image_id": image_id,
                "running_count": len(running_containers),
            }
        )
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete image: {len(running_containers)} running container(s) must be stopped first"
        )
    
    db.delete(image)
    db.commit()
    
    logger.info(
        "image.delete.success",
        extra={
            "image_id": image_id,
            "app_hostname": image.app_hostname,
            "user_id": user_id,
        }
    )