from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.utils.dependencies import get_user_id
from app.schemas.image import ImageCreate, ImageResponse, ImageWithContainers
from app.schemas.container import ContainerResponse
from app.schemas.common import ErrorResponse, MessageResponse, BuildLogsResponse
from app.application.services import image_service, container_service
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["images"])


@router.post(
    "/",
    response_model=ImageResponse,
    status_code=201,
    summary="Create Docker image",
    description="""
    Create a new Docker image from uploaded build context.
    
    Accepts a multipart/form-data upload containing:
    - A compressed archive (zip, tar, tar.gz, tgz) with the Dockerfile and build context
    - Image metadata (name, tag, app_hostname, resource limits, etc.)
    
    The image will be built asynchronously. Check the status field to track build progress.
    """,
    responses={
        201: {
            "description": "Image created successfully",
            "model": ImageResponse,
        },
        400: {
            "description": "Validation error or invalid file format",
            "model": ErrorResponse,
        },
        422: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
    },
)
async def create_image(
    name: str = Form(..., description="Image name (e.g., 'myapp')"),
    tag: str = Form(..., description="Image tag (e.g., 'latest', 'v1.0.0')"),
    app_hostname: str = Form(..., description="Application hostname identifier"),
    container_port: int = Form(
        8080, description="Container port to expose", ge=1, le=65535
    ),
    min_instances: int = Form(
        1, description="Minimum number of container instances", ge=1
    ),
    max_instances: int = Form(
        3, description="Maximum number of container instances", ge=1
    ),
    cpu_limit: str = Form("0.5", description="CPU limit (e.g., '0.5', '1.0', '2')"),
    memory_limit: str = Form(
        "512m", description="Memory limit (e.g., '512m', '1g', '2g')"
    ),
    file: UploadFile = File(
        ..., description="Compressed archive with Dockerfile and build context"
    ),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    """
    Create a new Docker image from uploaded build context.

    Args:
        name: Image name
        tag: Image tag/version
        app_hostname: Application hostname identifier
        container_port: Port to expose in the container
        min_instances: Minimum number of container instances
        max_instances: Maximum number of container instances
        cpu_limit: CPU resource limit
        memory_limit: Memory resource limit
        file: Compressed archive with Dockerfile and build context
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        ImageResponse: Created image information with build status
    """
    logger.info(
        "api.images.create.request",
        extra={
            "image_name": name,
            "image_tag": tag,
            "app_hostname": app_hostname,
            "upload_filename": file.filename,
            "content_type": file.content_type,
            "user_id": user_id,
        },
    )

    data = ImageCreate(
        user_id=user_id,
        name=name,
        tag=tag,
        app_hostname=app_hostname,
        container_port=container_port,
        min_instances=min_instances,
        max_instances=max_instances,
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
    )

    return await image_service.create_image_from_upload(
        db=db,
        data=data,
        file=file,
    )


@router.get(
    "/",
    response_model=List[ImageResponse],
    status_code=200,
    summary="List all images",
    description="List all Docker images registered by the current user.",
    responses={
        200: {
            "description": "List of images retrieved successfully",
            "model": List[ImageResponse],
        },
    },
)
async def list_images(
    db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    List all registered images for the current user.

    Args:
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        List[ImageResponse]: List of all images for the user
    """
    return image_service.get_all_images(db, user_id)


@router.get(
    "/with-containers",
    response_model=List[ImageWithContainers],
    status_code=200,
    summary="List images with containers",
    description="List all images with their associated containers for the current user.",
    responses={
        200: {
            "description": "List of images with containers retrieved successfully",
            "model": List[ImageWithContainers],
        },
    },
)
async def list_images_with_containers(
    db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    List all images with their containers for the current user.

    Args:
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        List[ImageWithContainers]: List of images with nested containers
    """
    return image_service.get_all_images_with_containers(db, user_id)


@router.get(
    "/{image_id}",
    response_model=ImageResponse,
    status_code=200,
    summary="Get image details",
    description="Retrieve detailed information about a specific image.",
    responses={
        200: {
            "description": "Image details retrieved successfully",
            "model": ImageResponse,
        },
        404: {
            "description": "Image not found",
            "model": ErrorResponse,
        },
    },
)
async def get_image(
    image_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Get a specific image by ID.

    Args:
        image_id: Image identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        ImageResponse: Image details
    """
    return image_service.get_image_by_id(db, image_id, user_id)


@router.get(
    "/{image_id}/build-logs",
    response_model=BuildLogsResponse,
    status_code=200,
    summary="Get build logs",
    description="Retrieve build logs for a specific image.",
    responses={
        200: {
            "description": "Build logs retrieved successfully",
            "model": BuildLogsResponse,
        },
        404: {
            "description": "Image not found",
            "model": ErrorResponse,
        },
    },
)
async def get_image_build_logs(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    """
    Get build logs for a specific image.

    Args:
        image_id: Image identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        BuildLogsResponse: Build logs for the image
    """
    image = image_service.get_image_by_id(db, image_id, user_id)
    return {"build_logs": image.build_logs or ""}


@router.get(
    "/{image_id}/containers",
    response_model=List[ContainerResponse],
    status_code=200,
    summary="Get image containers",
    description="List all containers associated with a specific image.",
    responses={
        200: {
            "description": "List of containers retrieved successfully",
            "model": List[ContainerResponse],
        },
        404: {
            "description": "Image not found",
            "model": ErrorResponse,
        },
    },
)
async def list_image_containers(
    image_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    List containers for a specific image.

    Args:
        image_id: Image identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        List[ContainerResponse]: List of containers for the image
    """
    return container_service.get_containers_of_image(db, user_id, image_id)


@router.delete(
    "/{image_id}",
    response_model=MessageResponse,
    status_code=200,
    summary="Delete image",
    description="Delete a specific image. All associated containers must be stopped first.",
    responses={
        200: {
            "description": "Image deleted successfully",
            "model": MessageResponse,
        },
        400: {
            "description": "Image has running containers",
            "model": ErrorResponse,
        },
        404: {
            "description": "Image not found",
            "model": ErrorResponse,
        },
    },
)
async def delete_image(
    image_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Delete an image.

    Args:
        image_id: Image identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        MessageResponse: Deletion confirmation message
    """
    image_service.delete_image(db, image_id, user_id)
    return {"message": f"Image {image_id} deleted successfully"}
