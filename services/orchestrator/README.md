# Orchestrator

Container lifecycle management service that builds Docker images, creates and manages containers, and emits Kafka events for service discovery and billing.

## Overview

The Orchestrator service is responsible for:
- Building Docker images from user-uploaded Dockerfiles (Cloud Run-style)
- Creating, starting, stopping, and deleting containers
- Managing container ports and networking (default internal port: 8080)
- Publishing container lifecycle events to Kafka
- Enforcing `max_instances` limits per image
- Storing build contexts and build logs persistently

## Features

- **Image Management**: Build Docker images from user-uploaded source code (zip/tar with Dockerfile)
- **Build Pipeline**: Automatic build on upload, with status tracking (`building` → `ready` / `build_failed`)
- **Build Logs**: Captures and stores Docker build output logs
- **Container Lifecycle**: Full CRUD operations for containers
- **Dynamic Port Assignment**: Automatically assigns available ports to containers
- **Port Contract**: User applications must listen on port 8080 (configurable via `container_port`)
- **Event Publishing**: Emits container lifecycle events to Kafka with `app_hostname`
- **Instance Limits**: Enforces maximum container instances per image
- **Unique Naming**: Prevents container naming conflicts with UUID suffixes
- **Unique Image Tagging**: Uses `nvidia-app-u{user_id}-i{image_id}:{tag}` to prevent collisions
- **Retry Logic**: Automatic retries for transient Docker API errors
- **Persistent Build Context**: Stores uploaded source code in persistent volume

## Endpoints

### Images
- `POST /api/images` - **Upload and build Docker image** (multipart/form-data)
  - Accepts: `name`, `tag`, `app_hostname`, `container_port` (default: 8080), `min_instances`, `max_instances`, `cpu_limit`, `memory_limit`, `file` (zip/tar with Dockerfile)
  - Returns: Image with status `building`, then updates to `ready` or `build_failed`
- `GET /api/images` - List all images for the authenticated user
- `GET /api/images/with-containers` - List images with container counts
- `GET /api/images/{image_id}` - Get image details (includes `status`, `build_logs`, `source_path`)
- `GET /api/images/{image_id}/build-logs` - Get build logs for an image
- `GET /api/images/{image_id}/containers` - List containers for an image
- `DELETE /api/images/{image_id}` - Delete an image

### Image Status
Images have the following status values:
- `building` - Image is currently being built
- `ready` - Image build completed successfully
- `build_failed` - Image build failed (check `build_logs` for details)
- `registered` - Legacy status (default for old images)

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
- Build Context Storage: `BUILD_CONTEXT_BASE_DIR` (default: `/var/lib/orchestrator/build-contexts`)

## Build Process

1. User uploads zip/tar file containing Dockerfile via `POST /api/images`
2. Orchestrator extracts archive to persistent storage (`{BUILD_CONTEXT_BASE_DIR}/{user_id}/{image_id}/context`)
3. Validates that Dockerfile exists at context root
4. Builds Docker image using `docker build` with unique tag: `nvidia-app-u{user_id}-i{image_id}:{tag}`
5. Captures build logs and stores in database (truncated to 8000 chars)
6. Updates image status: `building` → `ready` (or `build_failed` on error)
7. Source code is persisted for potential rebuilds

## Dependencies

- PostgreSQL: For image and container metadata
- Docker: For container runtime operations and image builds
- Kafka: For event publishing (events include `app_hostname`)
- Service Discovery: Registers containers via Kafka events
- Persistent Volume: For storing build contexts (mounted at `BUILD_CONTEXT_BASE_DIR`)
