from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.config import get_db
from app.schemas.container import ContainerCreate, ContainerResponse
from app.schemas.common import ErrorResponse, MessageResponse
from app.utils.dependencies import get_user_id
from app.application.services import container_service
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

router = APIRouter(tags=["containers"])
logger = setup_logger(SERVICE_NAME)


@router.post(
    "/{image_id}",
    response_model=List[ContainerResponse],
    status_code=201,
    summary="Create containers",
    description="Create and run containers from a specific image. Multiple containers can be created at once.",
    responses={
        201: {
            "description": "Containers created successfully",
            "model": List[ContainerResponse],
        },
        404: {
            "description": "Image not found",
            "model": ErrorResponse,
        },
        400: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
    },
)
async def create_containers(
    image_id: int,
    container_data: ContainerCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    """
    Create and run containers from a specific image.

    Args:
        image_id: Image identifier to create containers from
        container_data: Container creation data (name, count)
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        List[ContainerResponse]: List of created containers
    """
    return container_service.create_containers(db, image_id, user_id, container_data)


@router.post(
    "/{id}/start",
    response_model=ContainerResponse,
    status_code=200,
    summary="Start container",
    description="Start a stopped container.",
    responses={
        200: {
            "description": "Container started successfully",
            "model": ContainerResponse,
        },
        404: {
            "description": "Container not found",
            "model": ErrorResponse,
        },
        400: {
            "description": "Container is already running",
            "model": ErrorResponse,
        },
    },
)
async def start_container_endpoint(
    id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Start a stopped container.

    Args:
        id: Container identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        ContainerResponse: Updated container information
    """
    return container_service.start_container(db, user_id, id)


@router.post(
    "/{id}/stop",
    response_model=ContainerResponse,
    status_code=200,
    summary="Stop container",
    description="Stop a running container.",
    responses={
        200: {
            "description": "Container stopped successfully",
            "model": ContainerResponse,
        },
        404: {
            "description": "Container not found",
            "model": ErrorResponse,
        },
        400: {
            "description": "Container is already stopped",
            "model": ErrorResponse,
        },
    },
)
async def stop_container_endpoint(
    id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Stop a running container.

    Args:
        id: Container identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        ContainerResponse: Updated container information
    """
    return container_service.stop_container(db, user_id, id)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=200,
    summary="Delete container",
    description="Delete a container. The container will be stopped if it's running.",
    responses={
        200: {
            "description": "Container deleted successfully",
            "model": MessageResponse,
        },
        404: {
            "description": "Container not found",
            "model": ErrorResponse,
        },
    },
)
async def delete_container_endpoint(
    id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Delete a container.

    Args:
        id: Container identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        MessageResponse: Deletion confirmation message
    """
    return container_service.delete_container(db, user_id, id)


@router.get(
    "/",
    response_model=List[ContainerResponse],
    status_code=200,
    summary="List all containers",
    description="List all containers for the current user.",
    responses={
        200: {
            "description": "List of containers retrieved successfully",
            "model": List[ContainerResponse],
        },
    },
)
async def list_containers(
    db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    List all containers for the current user.

    Args:
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        List[ContainerResponse]: List of all containers for the user
    """
    return container_service.get_all_containers(db, user_id)
