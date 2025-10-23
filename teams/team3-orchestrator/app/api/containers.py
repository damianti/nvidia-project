from fastapi import APIRouter
from app.database.config import get_db
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException
from app.database.models import Image, Container, User
from typing import List
from app.schemas.container import ContainerCreate, ContainerResponse
import docker
from docker.errors import DockerException
from app.api.auth import get_current_user
router = APIRouter( tags=["containers"])



# Container endpoints
@router.post("/images/{image_id}/containers", response_model=List[ContainerResponse])
async def create_containers(
    image_id: int, 
    container_request: ContainerCreate, 
    db: Session = Depends(get_db)
):
    """Create containers for a specific image"""
    try:
        # Get image
        docker_client = docker.from_env()
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check current containers
        current_containers = db.query(Container).filter(Container.image_id == image_id).count()
        if current_containers + container_request.count > image.max_instances:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create {container_request.count} containers. "
                       f"Current: {current_containers}, Max: {image.max_instances}"
            )
        
        created_containers = []
        
        for i in range(container_request.count):
            try:
                # Assign dynamic port (starting from 4000 to avoid conflicts with UI)
                port = 4000 + current_containers + i
                
                # Create container
                container = docker_client.containers.run(
                    image=f"{image.name}:{image.tag}",
                    name=f"{image.name}-{image.tag}-{current_containers + i}",
                    ports={'80/tcp': port},  # Most web servers listen on port 80
                    detach=True,
                    environment={
                        'SERVICE_NAME': f"{image.name}-{image.tag}",
                        'CONTAINER_ID': f"{image.name}-{current_containers + i}"
                    }
                )
                
                # Save to database
                db_container = Container(
                    container_id=container.id,
                    name=container.name,
                    port=port,
                    image_id=image_id
                )
                db.add(db_container)
                created_containers.append(db_container)
                
            except DockerException as e:
                raise HTTPException(status_code=500, detail=f"Failed to create container: {str(e)}")
        
        db.commit()
        
        # Refresh containers to get IDs
        for container in created_containers:
            db.refresh(container)
        
        return created_containers
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ContainerResponse])
async def list_containers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """List all containers from the current user"""
    containers = db.query(Container)\
        .options(joinedload(Container.image))\
        .join(Image)\
        .filter(Image.user_id == current_user.id)\
        .all()
    return containers

@router.get("/images/{image_id}/containers", response_model=List[ContainerResponse])
async def list_image_containers(image_id: int, db: Session = Depends(get_db)):
    """List containers for a specific image"""
    containers = db.query(Container).filter(Container.image_id == image_id).all()
    return containers
