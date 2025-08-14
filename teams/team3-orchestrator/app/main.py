from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import docker
from docker.errors import DockerException

from app.database.config import get_db
from app.database.models import Image, Container, User, Billing
from app.schemas.image import ImageCreate, ImageResponse, ContainerCreate, ContainerResponse
from app.schemas.user import UserCreate, UserResponse

app = FastAPI(
    title="Orchestrator API",
    description="Container orchestration and management service",
    version="1.0.0"
)

# Docker client
docker_client = docker.from_env()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Orchestrator API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db = next(get_db())
        db.execute("SELECT 1")
        
        # Check Docker connection
        docker_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "docker": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# User endpoints
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password  # In production, hash the password!
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).all()
    return users

# Image endpoints
@app.post("/images/", response_model=ImageResponse)
async def create_image(image: ImageCreate, db: Session = Depends(get_db)):
    """Register a new Docker image"""
    try:
        # Verify image exists in Docker
        try:
            docker_image = docker_client.images.get(f"{image.name}:{image.tag}")
        except DockerException:
            raise HTTPException(
                status_code=404,
                detail=f"Image {image.name}:{image.tag} not found in Docker"
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

@app.get("/images/", response_model=List[ImageResponse])
async def list_images(db: Session = Depends(get_db)):
    """List all registered images"""
    images = db.query(Image).all()
    return images

@app.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, db: Session = Depends(get_db)):
    """Get a specific image"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.delete("/images/{image_id}")
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

# Container endpoints
@app.post("/images/{image_id}/containers", response_model=List[ContainerResponse])
async def create_containers(
    image_id: int, 
    container_request: ContainerCreate, 
    db: Session = Depends(get_db)
):
    """Create containers for a specific image"""
    try:
        # Get image
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
                # Assign dynamic port
                port = 3000 + current_containers + i
                
                # Create container
                container = docker_client.containers.run(
                    image=f"{image.name}:{image.tag}",
                    name=f"{image.name}-{image.tag}-{current_containers + i}",
                    ports={'3000/tcp': port},
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

@app.get("/containers/", response_model=List[ContainerResponse])
async def list_containers(db: Session = Depends(get_db)):
    """List all containers"""
    containers = db.query(Container).all()
    return containers

@app.get("/images/{image_id}/containers", response_model=List[ContainerResponse])
async def list_image_containers(image_id: int, db: Session = Depends(get_db)):
    """List containers for a specific image"""
    containers = db.query(Container).filter(Container.image_id == image_id).all()
    return containers

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


