from fastapi import APIRouter
from app.database.config import get_db
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException
from app.database.models import Image, Container
from typing import List
from app.schemas.image import ImageCreate, ImageResponse, ImageWithContainers
from app.services.docker_service import build_image
from app.api.auth import get_current_user
from app.database.models import User

router = APIRouter(tags=["images"])


@router.post("/", response_model=ImageResponse)
async def create_image(image: ImageCreate, db: Session = Depends(get_db)):
    """Register a new Docker image"""
    try:
        
        build_image(image.name, image.tag, image.website_url, image.user_id)
        # Create image record
        db_image = Image(
            name=image.name,
            tag=image.tag,
            website_url = image.website_url,
            min_instances=image.min_instances,
            max_instances=image.max_instances,
            cpu_limit=image.cpu_limit,
            memory_limit=image.memory_limit,
            user_id=image.user_id
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ImageResponse])
async def list_images(db: Session = Depends(get_db)):
    """List all registered images"""
    images = db.query(Image).all()
    return images

@router.get("/with-containers", response_model=List[ImageWithContainers])
async def list_images_with_containers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ List all images with their container for the current user"""
    images = db.query(Image)\
        .options(joinedload(Image.containers))\
        .filter(Image.user_id == current_user.id)\
        .all()
    
    return images


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, db: Session = Depends(get_db)):
    """Get a specific image"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@router.delete("/{image_id}")
async def delete_image(image_id: int, db: Session = Depends(get_db)):
    """Delete an image"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if containers are running
    containers = db.query(Container).filter(Container.image_id == image_id).all()
    if containers:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete image with running containers"
        )
    
    db.delete(image)
    db.commit()
    return {"message": f"Image {image_id} deleted successfully"}



