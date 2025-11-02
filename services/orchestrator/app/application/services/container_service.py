from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict
import logging


from app.database.models import Container, User, ContainerStatus
from app.schemas.container import ContainerCreate
from app.services import docker_service
from app.services.kafka_producer import KafkaProducerSingleton
from app.repositories import containers_repository, images_repository


logger = logging.getLogger("orchestrator")

def create_containers(db: Session, image_id: int, current_user: User, container_data: ContainerCreate) -> List[Container]:
    """ Create and run containers from a specific image """
    try:
        website_url = images_repository.get_by_id(db, image_id, current_user).website_url
        created_containers = []
        for _ in range(container_data.count):

            docker_container, external_port = docker_service.run_container(
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

            containers_repository.create(db, db_container)
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
                        "container_name": db_container.name,  # Nombre del container para usar como hostname
                        "image_id": db_container.image_id,
                        "port": db_container.external_port,
                        "website_url": website_url
                    }
                )
            except Exception as e:
                logger.error(f"Failed to publish to Kafka: {e}")

        return created_containers

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating containers: {e}", exc_info=True)
        raise HTTPException(status_code = 500, detail=f"Error creating containers: {str(e)}")

def start_container(db: Session, current_user: User, container_id: int):
    db_container = containers_repository.get_by_id_and_user(db, container_id, current_user.id)
    
    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    docker_service.start_container(db_container.container_id)
    db_container.status = ContainerStatus.RUNNING
    db.commit()
    db.refresh(db_container)
    try:
        image = images_repository.get_by_id(db, db_container.image_id, current_user)
        website_url = image.website_url if image else None
        KafkaProducerSingleton.instance().produce_json(
            topic="container-lifecycle",
            key=str(db_container.image_id),
            value={
                "event": "container.started",
                "container_id": db_container.container_id,
                "container_name": db_container.name,  # Nombre del container para usar como hostname
                "image_id": db_container.image_id,
                "port": db_container.external_port,
                **({"website_url": website_url} if website_url else {})
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")

    return db_container


def stop_container(db: Session, current_user: User, container_id: int):
    db_container = containers_repository.get_by_id_and_user(db, container_id, current_user.id)
    
    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")
    
    docker_service.stop_container(db_container.container_id)
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
                "port": db_container.external_port,
                
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")

    return db_container

def delete_container(db: Session, current_user: User, container_id: int) -> Dict[str, str]:
    db_container = containers_repository.get_by_id_and_user(db, container_id, current_user.id)

    if not db_container:
        raise HTTPException(status_code=404, detail=f"container {container_id} not found")

    container_data = {
            "container_id": db_container.container_id,
            "image_id": db_container.image_id,
            "port": db_container.external_port
    }

    docker_service.delete_container(db_container.container_id)
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


def get_all_containers(db: Session, current_user: User) -> List[Container]:
    return containers_repository.list_by_user(db, current_user.id)


def get_containers_of_image(db: Session, current_user: User, image_id: int) -> List[Container]:
    return containers_repository.list_by_image_and_user(db, image_id, current_user.id)
