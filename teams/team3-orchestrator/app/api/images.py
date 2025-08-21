from fastapi import APIRouter
from app.database.config import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.database.models import Image, Container
from typing import List
from app.schemas.image import ImageCreate, ImageResponse
import docker
from docker.errors import DockerException

docker_client = docker.from_env()
router = APIRouter(prefix="/images", tags=["images"])


@router.post("/", response_model=ImageResponse)
async def create_image(image: ImageCreate, db: Session = Depends(get_db)):
    """Register a new Docker image"""
    try:
        # Verify image exists in Docker, download if not found
        try:
            docker_image = docker_client.images.get(f"{image.name}:{image.tag}")
        except DockerException:
            # Try to pull the image from Docker Hub
            try:
                print(f"Downloading image {image.name}:{image.tag} from Docker Hub...")
                docker_image = docker_client.images.pull(f"{image.name}:{image.tag}")
                print(f"Successfully downloaded {image.name}:{image.tag}")
            except DockerException as pull_error:
                raise HTTPException(
                    status_code=404,
                    detail=f"Image {image.name}:{image.tag} not found in Docker Hub: {str(pull_error)}"
                )
        
        # Create image record
        db_image = Image(
            name=image.name,
            tag=image.tag,
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



