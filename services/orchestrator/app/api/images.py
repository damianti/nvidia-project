from fastapi import APIRouter
from app.database.config import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List

from app.utils.dependencies import get_user_id
from app.schemas.image import ImageCreate, ImageResponse, ImageWithContainers
from app.schemas.container import ContainerResponse
from app.application.services import image_service, container_service

router = APIRouter(tags=["images"])


@router.post("/", response_model=ImageResponse, summary="Create a new image")
async def create_image(image: ImageCreate, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Register a new Docker image"""
    return image_service.create_image(db, image, user_id)
        


@router.get("/", response_model=List[ImageResponse], summary="List all images")
async def list_images(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """List all registered images"""
    return image_service.get_all_images(db, user_id)



@router.get("/with-containers", response_model=List[ImageWithContainers], summary="List images with their containers")
async def list_images_with_containers(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """List all images with their containers for the current user"""
    return image_service.get_all_images_with_containers(db, user_id)
    


@router.get("/{image_id}", response_model=ImageResponse, summary="Get image details")
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Get a specific image"""
    return image_service.get_image_by_id(db, image_id, user_id)


@router.get("/{image_id}/containers", response_model=List[ContainerResponse], summary="Get containers for an image")
async def list_image_containers(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """List containers for a specific image"""
    return container_service.get_containers_of_image(db, user_id, image_id)
    

@router.delete("/{image_id}", summary="Delete an image")
async def delete_image(image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Delete an image"""
    image_service.delete_image(db, image_id, user_id)
    return {"message": f"Image {image_id} deleted successfully"}



