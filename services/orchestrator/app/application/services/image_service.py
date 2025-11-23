from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional

from app.schemas.image import ImageCreate
from app.database.models import Image, ContainerStatus
from app.repositories import images_repository, containers_repository
from app.services.docker_service import build_image


def create_image(db: Session, payload: ImageCreate, user_id: int) -> Image:
    """Creates an Image: validates duplicates, builds in Docker, persists and confirms."""
    try:
        existing = images_repository.get_by_website_url(
            db,
            website_url = payload.website_url,
            user_id = user_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="Image with same website_url already exists for this user")

        build_image(payload.name, payload.tag, payload.website_url, user_id)

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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 

def get_all_images(db: Session, user_id: int):
    return images_repository.get_all_images(db, user_id)

def get_all_images_with_containers(db: Session, user_id: int):
    return images_repository.get_all_images_with_containers(db, user_id)

def get_image_by_id (db: Session, image_id: int, user_id: int) -> Optional[Image]:
    image = images_repository.get_by_id(db, image_id, user_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return image


def delete_image (db: Session, image_id: int, user_id: int):
    image = get_image_by_id(db, image_id, user_id)
    
    containers = containers_repository.get_containers_by_image_id(db, image_id)
    
    if any (c.status == ContainerStatus.RUNNING for c in containers):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete image with running containers"
        )
    
    db.delete(image)
    db.commit()