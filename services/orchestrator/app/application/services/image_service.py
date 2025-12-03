from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional

from app.schemas.image import ImageCreate
from app.database.models import Image, ContainerStatus
from app.repositories import images_repository, containers_repository
from app.services.docker_service import build_image


def create_image(db: Session, payload: ImageCreate, user_id: int) -> Image:
    """
    Creates an Image: validates duplicates, builds in Docker, persists and confirms.
    
    Args:
        db: Database session
        payload: Image creation data
        user_id: ID of the user creating the image
    
    Returns:
        Created Image object
    
    Raises:
        HTTPException: 400 if image with same website_url exists, 500 on build failure
    """
    try:
        # Validate duplicate website_url for this user
        existing = images_repository.get_by_website_url(
            db,
            website_url=payload.website_url,
            user_id=user_id
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Image with website_url '{payload.website_url}' already exists for this user"
            )

        # Build Docker image
        build_image(payload.name, payload.tag, payload.website_url, user_id)

        # Create database record
        db_image = Image(
            name=payload.name,
            tag=payload.tag,
            website_url=payload.website_url,
            min_instances=payload.min_instances,
            max_instances=payload.max_instances,
            cpu_limit=payload.cpu_limit,
            memory_limit=payload.memory_limit,
            user_id=user_id,
        )

        images_repository.create(db, db_image)
        db.commit()
        db.refresh(db_image)
        return db_image

    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate check)
        db.rollback()
        raise
    except Exception as e:
        # Rollback and return generic error (don't expose internal details)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create image. Please check image name and tag are valid."
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
    image = get_image_by_id(db, image_id, user_id)
    
    containers = containers_repository.get_containers_by_image_id(db, image_id)
    
    running_containers = [c for c in containers if c.status == ContainerStatus.RUNNING]
    if running_containers:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete image: {len(running_containers)} running container(s) must be stopped first"
        )
    
    db.delete(image)
    db.commit()