from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from typing import List
from datetime import datetime 

from app.database.config import get_db
from app.database.models import Container, User
from app.schemas.container import ContainerCreate, ContainerResponse
from app.api.auth import get_current_user
from app.services.docker_service import run_container, start_container, stop_container, delete_container

router = APIRouter( tags=["containers"])

@router.post("/{image_id}/create", response_model=List[ContainerResponse])
async def create_containers(
    image_id: int,
    container: ContainerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Create and run containers from a specific image """
    try:
        created_containers = []
        for count in range(container.count):
            port_to_run = 4000 + count # TODO get a better port number
            docker_container = run_container(
                image_name = "nginx",
                image_tag = "latest",
                container_name =container.name,
                port = port_to_run,
                env_vars = {} )

            db_container = Container(
                container_id = docker_container.id,
                name = docker_container.name,
                port = port_to_run,
                status = "running",
                cpu_usage = "0.0",
                memory_usage = "0m",
                image_id = image_id,
                user_id = current_user.id)

            db.add(db_container)
            created_containers.append(db_container)
        
        db.commit()
        for c in created_containers:
            db.refresh(c)
        
        return created_containers
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail=str(e))

@router.post("/{container_id}/start", response_model = ContainerResponse)
async def start_containers_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Start a stopped container """

    container = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .filter(Container.id == container_id)\
        .first()
    
    if not container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    start_container(container.container_id)
    container.status = "running"
    db.commit()
    db.refresh(container)

    return container

@router.post("/{container_id}/stop", response_model = ContainerResponse)
async def stop_containers_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Stop a started container """

    container = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .filter(Container.id == container_id)\
        .first()
    
    if not container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    stop_container(container.container_id)
    container.status = "stopped"
    db.commit()
    db.refresh(container)
    

    return container

@router.delete("/{container_id}")
async def delete_containers_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Delete a container """
    container = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .filter(Container.id == container_id)\
        .first()

    if not container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")

    delete_container(container.container_id)

    db.delete(container)
    db.commit()

    return {"message": f"Container {container_id} deleted successfully"}
    

@router.get("/", response_model=List[ContainerResponse])
async def list_containers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """List all containers from the current user"""
    containers = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .all()

    return containers

@router.get("/images/{image_id}/containers", response_model=List[ContainerResponse])
async def list_image_containers(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):

    """List containers for a specific image"""
    containers = db.query(Container)\
        .filter(Container.image_id == image_id)\
        .filter(Container.user_id == current_user.id)\
        .all()
    return containers
