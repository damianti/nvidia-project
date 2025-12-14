# Orchestrator

Container lifecycle management service that builds Docker images, creates and manages containers, and emits Kafka events for service discovery and billing.

## Overview

The Orchestrator service is responsible for:
- Building Docker images from Dockerfiles
- Creating, starting, stopping, and deleting containers
- Managing container ports and networking
- Publishing container lifecycle events to Kafka
- Enforcing `max_instances` limits per image

## Features

- **Image Management**: Build and store Docker images
- **Container Lifecycle**: Full CRUD operations for containers
- **Dynamic Port Assignment**: Automatically assigns available ports to containers
- **Event Publishing**: Emits container lifecycle events to Kafka
- **Instance Limits**: Enforces maximum container instances per image
- **Unique Naming**: Prevents container naming conflicts with UUID suffixes
- **Retry Logic**: Automatic retries for transient Docker API errors

## Endpoints

### Images
- `POST /api/images` - Create a new Docker image
- `GET /api/images` - List all images
- `GET /api/images/with-containers` - List images with container counts
- `GET /api/images/{image_id}` - Get image details
- `GET /api/images/{image_id}/containers` - List containers for an image
- `DELETE /api/images/{image_id}` - Delete an image

### Containers
- `POST /api/containers/{image_id}` - Create containers from an image
- `GET /api/containers/` - List all containers
- `GET /api/containers/{id}` - Get container details
- `POST /api/containers/{id}/start` - Start a container
- `POST /api/containers/{id}/stop` - Stop a container
- `DELETE /api/containers/{id}` - Delete a container

## Configuration

- Port: `3003`
- Database: PostgreSQL
- Docker: Docker-in-Docker (DinD) integration
- Kafka: Publishes to `container-lifecycle` topic

## Dependencies

- PostgreSQL: For image and container metadata
- Docker: For container runtime operations
- Kafka: For event publishing
- Service Discovery: Registers containers via Kafka events
