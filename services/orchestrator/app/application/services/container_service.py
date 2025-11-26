from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict
from datetime import datetime, timezone
import logging


from app.database.models import Container, ContainerStatus
from app.schemas.container import ContainerCreate
from app.services import docker_service
from app.services.kafka_producer import KafkaProducerSingleton
from app.repositories import containers_repository, images_repository


logger = logging.getLogger("orchestrator")

def create_containers(db: Session, image_id: int, user_id: int, container_data: ContainerCreate) -> List[Container]:
    """ Create and run containers from a specific image """
    try:
        website_url = images_repository.get_by_id(db, image_id, user_id).website_url
        created_containers = []
        for _ in range(container_data.count):

            docker_container, external_port, container_ip = docker_service.run_container(
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
                container_ip = container_ip,
                image_id = image_id,
                user_id = user_id)

            containers_repository.create(db, db_container)
            created_containers.append(db_container)
        
        db.commit()
        for db_container in created_containers:
            db.refresh(db_container)
        
        for db_container in created_containers:
            try:
                
                KafkaProducerSingleton.instance().produce_json(
                    topic="container-lifecycle",
                    key=str(db_container.image_id),
                    value={
                        "event": "container.created",
                        "user_id": db_container.user_id,
                        "container_id": db_container.container_id,
                        "container_name": db_container.name,
                        "container_ip": db_container.container_ip,
                        "image_id": db_container.image_id,
                        "internal_port": db_container.internal_port,
                        "port": db_container.external_port,
                        "website_url": website_url,
                        "timestamp": datetime.now(timezone.utc)
                    }
                )
            except Exception as e:
                logger.error(
                    "kafka.publish_failed",
                    extra={
                        "event": "container.created",
                        "container_id": db_container.container_id,
                        "container_name": db_container.name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )

        return created_containers

    except Exception as e:
        db.rollback()
        logger.error(
            "container.create_failed",
            extra={
                "image_id": image_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error creating containers: {str(e)}")

def start_container(db: Session, user_id: int, container_id: int):
    db_container = containers_repository.get_by_id_and_user(db, container_id, user_id)
    
    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    docker_service.start_container(db_container.container_id)
    db_container.status = ContainerStatus.RUNNING
    db.commit()
    db.refresh(db_container)
    try:
        image = images_repository.get_by_id(db, db_container.image_id, user_id)
        website_url = image.website_url if image else None
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key=str(db_container.image_id),
            value={
                "event": "container.started",
                "user_id": db_container.user_id,
                "container_id": db_container.container_id,
                "container_ip": db_container.container_ip,
                "container_name": db_container.name,
                "image_id": db_container.image_id,
                "internal_port": db_container.internal_port,
                "port": db_container.external_port,
                "website_url": website_url,
                "timestamp": datetime.now(timezone.utc)
            }
        )
    except Exception as e:
        logger.error(
            "kafka.publish_failed",
            extra={
                "event": "container.started",
                "container_id": db_container.container_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

    return db_container


def stop_container(db: Session, user_id: int, container_id: int):
    db_container = containers_repository.get_by_id_and_user(db, container_id, user_id)
    
    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    docker_service.stop_container(db_container.container_id)
    db_container.status = ContainerStatus.STOPPED
    db.commit()
    db.refresh(db_container)
    try:
        image = images_repository.get_by_id(db, db_container.image_id, user_id)
        website_url = image.website_url if image else None
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key=str(db_container.image_id),
            value={
                "event": "container.stopped",
                "user_id": db_container.user_id,
                "container_id": db_container.container_id,
                "container_name": db_container.name,
                "container_ip": db_container.container_ip,
                "image_id": db_container.image_id,
                "internal_port": db_container.internal_port,
                "port": db_container.external_port,
                "website_url": website_url,
                "timestamp": datetime.now(timezone.utc)
            }
        )
    except Exception as e:
        logger.error(
            "kafka.publish_failed",
            extra={
                "event": "container.stopped",
                "container_id": db_container.container_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

    return db_container

def delete_container(db: Session, user_id: int, container_id: int) -> Dict[str, str]:
    db_container = containers_repository.get_by_id_and_user(db, container_id, user_id)

    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")

    # Capture data before deleting
    image = images_repository.get_by_id(db, db_container.image_id, user_id)
    website_url = image.website_url if image else None
    container_data = {
        "user_id": db_container.user_id,
        "container_id": db_container.container_id,
        "container_name": db_container.name,
        "container_ip": db_container.container_ip,
        "image_id": db_container.image_id,
        "internal_port": db_container.internal_port,
        "port": db_container.external_port,
        "website_url": website_url,
        "timestamp": datetime.now(timezone.utc)
    }

    docker_service.delete_container(db_container.container_id)
    db.delete(db_container)
    db.commit()
    try:
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key=str(container_data["image_id"]),
            value={
                "event": "container.deleted",
                "user_id": container_data["user_id"],
                "container_id": container_data["container_id"],
                "container_name": container_data["container_name"],
                "container_ip": container_data["container_ip"],
                "image_id": container_data["image_id"],
                "internal_port": container_data["internal_port"],
                "port": container_data["port"],
                "website_url": container_data["website_url"],
                "timestamp": container_data["timestamp"]
            }
        )
    except Exception as e:
        logger.error(
            "kafka.publish_failed",
            extra={
                "event": "container.deleted",
                "container_id": container_data["container_id"],
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

    return {"message": f"Container {container_id} deleted successfully"}


def get_all_containers(db: Session, user_id: int) -> List[Container]:
    return containers_repository.list_by_user(db, user_id)


def get_containers_of_image(db: Session, user_id: int, image_id: int) -> List[Container]:
    return containers_repository.list_by_image_and_user(db, image_id, user_id)
