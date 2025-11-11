from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database.config import get_db
from app.schemas.container import ContainerCreate, ContainerResponse
from app.utils.dependencies import get_user_id
from app.application.services import container_service



router = APIRouter( tags=["containers"])
logger = logging.getLogger("orchestrator")


@router.post("/{image_id}/create", response_model=List[ContainerResponse])
async def create_containers(
    image_id: int,
    container_data: ContainerCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """ Create and run containers from a specific image """
    return container_service.create_containers(db, image_id, user_id, container_data)
    

@router.post("/{container_id}/start", response_model = ContainerResponse)
async def start_container_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """ Start a stopped container """
    return container_service.start_container(db, user_id, container_id)
    

@router.post("/{container_id}/stop", response_model = ContainerResponse)
async def stop_container_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """ Stop a started container """
    return container_service.stop_container(db, user_id, container_id)
    

@router.delete("/{container_id}")
async def delete_container_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """ Delete a container """
    return container_service.delete_container(db, user_id, container_id)
    
    

@router.get("/", response_model=List[ContainerResponse])
async def list_containers(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """List all containers from the current user"""
    return container_service.get_all_containers(db, user_id)
    

@router.get("/images/{image_id}/containers", response_model=List[ContainerResponse])
async def list_image_containers(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):

    """List containers for a specific image"""
    return container_service.get_containers_of_image(db, user_id, image_id)
    
