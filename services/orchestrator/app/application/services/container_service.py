from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict
from datetime import datetime, timezone
import logging
import uuid


from app.database.models import Container, ContainerStatus
from app.schemas.container import ContainerCreate
from app.services import docker_service
from app.services.kafka_producer import KafkaProducerSingleton
from app.repositories import containers_repository, images_repository


logger = logging.getLogger("orchestrator")

def create_containers(db: Session, image_id: int, user_id: int, container_data: ContainerCreate) -> List[Container]:
    """
    Create and start multiple container instances from a Docker image.
    
    This function:
    1. Retrieves the image metadata (including app_hostname)
    2. Creates the specified number of containers using Docker-in-Docker
    3. Persists container records to the database
    4. Publishes container.created events to Kafka for Service Discovery and Billing
    
    Args:
        db: Database session
        image_id: ID of the image to create containers from
        user_id: ID of the user creating the containers
        container_data: Container creation request (name, count)
    
    Returns:
        List of created Container objects
    
    Raises:
        HTTPException: 404 if image not found, 400 if invalid count, 500 if container creation fails
    """
    try:
        # Validate image exists and belongs to user
        image = images_repository.get_by_id(db, image_id, user_id)
        if not image:
            raise HTTPException(
                status_code=404,
                detail=f"Image with id {image_id} not found or access denied"
            )
        
        
        # Check max_instances limit (count ALL containers, not just RUNNING)
        existing_containers = containers_repository.get_containers_by_image_id(db, image_id)
        existing_count = len(existing_containers)
        max_allowed = image.max_instances - existing_count
        
        if max_allowed <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create containers: image already has {existing_count} containers (max: {image.max_instances})"
            )
        
        # Adjust count if requested count exceeds max_allowed
        actual_count = min(container_data.count, max_allowed)
        if actual_count < container_data.count:
            logger.warning(
                "container.count_adjusted",
                extra={
                    "image_id": image_id,
                    "user_id": user_id,
                    "requested_count": container_data.count,
                    "actual_count": actual_count,
                    "existing_count": existing_count,
                    "max_instances": image.max_instances
                }
            )
        
        app_hostname = image.app_hostname
        created_containers = []
        for i in range(actual_count):
            
            unique_suffix = uuid.uuid4().hex[:8]
            unique_container_name = f"{container_data.name}-{unique_suffix}"

            docker_container, external_port, container_ip = docker_service.run_container(
                image_name = "nginx",
                image_tag = "latest",
                container_name = unique_container_name,
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
                        "external_port": db_container.external_port,
                        "app_hostname": app_hostname,
                        "timestamp": datetime.now(timezone.utc).isoformat()
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

    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        db.rollback()
        raise
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
        raise HTTPException(
            status_code=500,
            detail="Failed to create containers. Please try again or contact support."
        ) from e

def start_container(db: Session, user_id: int, container_id: int):
    """
    Start a stopped container and publish container.started event.
    
    Args:
        db: Database session
        user_id: ID of the user owning the container
        container_id: ID of the container to start
    
    Returns:
        Updated Container object
    
    Raises:
        HTTPException: 404 if container not found, 400 if already running
    """
    db_container = containers_repository.get_by_id_and_user(db, container_id, user_id)
    
    if not db_container:
        raise HTTPException(
            status_code=404,
            detail=f"Container with id {container_id} not found or access denied"
        )
    
    # Validate container is not already running
    if db_container.status == ContainerStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Container {container_id} is already running"
        )
    
    try:
        docker_container, external_port, container_ip = docker_service.start_container(db_container.container_id)
        db_container.status = ContainerStatus.RUNNING
        # Update port and IP in case they changed after restart
        db_container.external_port = external_port
        db_container.container_ip = container_ip
    except Exception as e:
        logger.error(
            "container.start_docker_failed",
            extra={
                "container_id": container_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start container {container_id}. Docker service may be unavailable."
        ) from e
    db.commit()
    db.refresh(db_container)
    try:
        image = images_repository.get_by_id(db, db_container.image_id, user_id)
        app_hostname = image.app_hostname if image else None
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
                "external_port": db_container.external_port,
                "app_hostname": app_hostname,
                "timestamp": datetime.now(timezone.utc).isoformat()
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
    """
    Stop a running container and publish container.stopped event.
    
    Args:
        db: Database session
        user_id: ID of the user owning the container
        container_id: ID of the container to stop
    
    Returns:
        Updated Container object with STOPPED status
    
    Raises:
        HTTPException: 404 if container not found
    """
    db_container = containers_repository.get_by_id_and_user(db, container_id, user_id)
    
    if not db_container:
        raise HTTPException(
            status_code=404,
            detail=f"Container with id {container_id} not found or access denied"
        )
    
    # Validate container is not already stopped
    if db_container.status == ContainerStatus.STOPPED:
        raise HTTPException(
            status_code=400,
            detail=f"Container {container_id} is already stopped"
        )
    
    try:
        docker_service.stop_container(db_container.container_id)
        db_container.status = ContainerStatus.STOPPED
    except Exception as e:
        logger.error(
            "container.stop_docker_failed",
            extra={
                "container_id": container_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop container {container_id}. Docker service may be unavailable."
        ) from e
    db.commit()
    db.refresh(db_container)
    try:
        image = images_repository.get_by_id(db, db_container.image_id, user_id)
        app_hostname = image.app_hostname if image else None
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
                "external_port": db_container.external_port,
                "app_hostname": app_hostname,
                "timestamp": datetime.now(timezone.utc).isoformat()
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
    """
    Delete a container and publish container.deleted event.
    
    This function:
    1. Stops and removes the Docker container
    2. Deletes the database record
    3. Publishes container.deleted event to Kafka
    
    Args:
        db: Database session
        user_id: ID of the user owning the container
        container_id: ID of the container to delete
    
    Returns:
        Dictionary with deletion confirmation message
    
    Raises:
        HTTPException: 404 if container not found
    """
    db_container = containers_repository.get_by_id_and_user(db, container_id, user_id)

    if not db_container:
        raise HTTPException(
            status_code=404,
            detail=f"Container with id {container_id} not found or access denied"
        )

    # Capture data before deleting
    image = images_repository.get_by_id(db, db_container.image_id, user_id)
    app_hostname = image.app_hostname if image else None
    container_data = {
        "user_id": db_container.user_id,
        "container_id": db_container.container_id,
        "container_name": db_container.name,
        "container_ip": db_container.container_ip,
        "image_id": db_container.image_id,
        "internal_port": db_container.internal_port,
        "external_port": db_container.external_port,
        "app_hostname": app_hostname,
        "timestamp": datetime.now(timezone.utc).isoformat()
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
                "external_port": container_data["external_port"],
                "app_hostname": container_data["app_hostname"],
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
