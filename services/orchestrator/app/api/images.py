from fastapi import APIRouter
from app.database.config import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List

from app.schemas.image import ImageCreate, ImageResponse, ImageWithContainers
from app.api.auth import get_current_user
from app.database.models import User

from app.application.services import image_service 

router = APIRouter(tags=["images"])


@router.post("/", response_model=ImageResponse)
async def create_image(image: ImageCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new Docker image"""
    return image_service.create_image(db, image, current_user)
        


@router.get("/", response_model=List[ImageResponse])
async def list_images(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all registered images"""
    return image_service.get_all_images(db, current_user)



@router.get("/with-containers", response_model=List[ImageWithContainers])
async def list_images_with_containers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ List all images with their container for the current user"""
    return image_service.get_all_images_with_containers(db, current_user)
    


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific image"""
    return image_service.get_image_by_id(db, image_id, current_user)
    
    

@router.delete("/{image_id}")
async def delete_image(image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an image"""
    image_service.delete_image(db, image_id, current_user)
    return {"message": f"Image {image_id} deleted successfully"}



