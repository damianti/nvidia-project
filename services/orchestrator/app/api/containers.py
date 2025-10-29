from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime 
import logging

from app.database.config import get_db
from app.database.models import Container, User, ContainerStatus
from app.schemas.container import ContainerCreate, ContainerResponse
from app.api.auth import get_current_user
from app.services.docker_service import run_container, start_container, stop_container, delete_container
from app.services.kafka_producer import KafkaProducerSingleton

router = APIRouter( tags=["containers"])
logger = logging.getLogger(__name__)


@router.post("/{image_id}/create", response_model=List[ContainerResponse])
async def create_containers(
    image_id: int,
    container_data: ContainerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Create and run containers from a specific image """
    try:
        
        created_containers = []
        for _ in range(container_data.count):

            docker_container, external_port = run_container(
                image_name = "nginx",
                image_tag = "latest",
                container_name =container_data.name,
                env_vars = {} )
            
            db_container = Container(
                container_id = docker_container.id,
                name = docker_container.name,
                status = ContainerStatus.RUNNING,
                cpu_usage = "0.0",
                memory_usage = "0m",
                internal_port = 80,
                external_port = external_port,
                image_id = image_id,
                user_id = current_user.id)

            db.add(db_container)
            created_containers.append(db_container)
        
        db.commit()
        for db_container in created_containers:
            db.refresh(db_container)
        
        for db_container in created_containers:
            try:
                KafkaProducerSingleton.instance().produce_json(
                    topic="container-lifecycle",
                    key= str(db_container.image_id),
                    value ={
                        "event": "container.created",
                        "container_id": db_container.container_id,
                        "image_id": db_container.image_id,
                        "port": db_container.external_port
                    }
                )
            except Exception as e:
                logger.error(f"Failed to publish to Kafka: {e}")

        return created_containers
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail=str(e))

@router.post("/{container_id}/start", response_model = ContainerResponse)
async def start_container_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Start a stopped container """

    db_container = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .filter(Container.id == container_id)\
        .first()
    
    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    start_container(db_container.container_id)
    db_container.status = ContainerStatus.RUNNING
    db.commit()
    db.refresh(db_container)
    try:
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key=str(db_container.image_id),
            value={
                "event": "container.started",
                "container_id": db_container.container_id,
                "image_id": db_container.image_id,
                "port": db_container.external_port
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")

    return db_container

@router.post("/{container_id}/stop", response_model = ContainerResponse)
async def stop_container_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Stop a started container """

    db_container = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .filter(Container.id == container_id)\
        .first()
    
    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    stop_container(db_container.container_id)
    db_container.status = ContainerStatus.STOPPED
    db.commit()
    db.refresh(db_container)
    try:
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key=str(db_container.image_id),
            value={
                "event": "container.stopped",
                "container_id": db_container.container_id,
                "image_id": db_container.image_id,
                "port": db_container.external_port
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")

    return db_container

@router.delete("/{container_id}")
async def delete_container_endpoint(
    container_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """ Delete a container """
    db_container = db.query(Container)\
        .filter(Container.user_id == current_user.id)\
        .filter(Container.id == container_id)\
        .first()

    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")

    container_data = {
            "container_id": db_container.container_id,
            "image_id": db_container.image_id,
            "port": db_container.external_port
    }

    delete_container(db_container.container_id)
    db.delete(db_container)
    db.commit()
    try:
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key= str(container_data["image_id"]),
            value= {
                "event": "container.deleted",
                "container_id": container_data["container_id"],
                "image_id": container_data["image_id"],
                "port": container_data["port"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")

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
