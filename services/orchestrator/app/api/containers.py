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


@router.post("/{image_id}", response_model=List[ContainerResponse], summary="Create containers from an image")
async def create_containers(
    image_id: int,
    container_data: ContainerCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """Create and run containers from a specific image"""
    return container_service.create_containers(db, image_id, user_id, container_data)
    

@router.post("/{id}/start", response_model=ContainerResponse, summary="Start a stopped container")
async def start_container_endpoint(
    id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """Start a stopped container"""
    return container_service.start_container(db, user_id, id)
    

@router.post("/{id}/stop", response_model=ContainerResponse, summary="Stop a running container")
async def stop_container_endpoint(
    id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """Stop a running container"""
    return container_service.stop_container(db, user_id, id)
    

@router.delete("/{id}", summary="Delete a container")
async def delete_container_endpoint(
    id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """Delete a container"""
    return container_service.delete_container(db, user_id, id)
    
    

@router.get("/", response_model=List[ContainerResponse], summary="List all containers")
async def list_containers(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)):
    """List all containers from the current user"""
    return container_service.get_all_containers(db, user_id)
    
