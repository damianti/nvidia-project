"""FastAPI application configuration."""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints for service monitoring",
    },
    {
        "name": "images",
        "description": "Docker image management operations",
    },
    {
        "name": "containers",
        "description": "Container lifecycle management operations",
    },
]

APP_DESCRIPTION = """
Container and Image Orchestration Service for NVIDIA Cloud Platform.

This service manages the complete lifecycle of Docker containers and images, providing:

* **Image Management**: Upload, build, and manage Docker images
* **Container Management**: Create, start, stop, and delete containers
* **Build Logs**: Track image build progress and logs
* **Resource Management**: Configure CPU and memory limits for containers

## Features

- Docker image building from source code archives
- Container lifecycle management (create, start, stop, delete)
- Automatic container scaling based on min/max instances
- Resource limits (CPU, memory) per container
- Build log tracking and retrieval
- Integration with Service Discovery and Kafka for event publishing

## Documentation

- **Swagger UI**: Available at `/docs` (interactive API documentation)
- **ReDoc**: Available at `/redoc` (alternative documentation format)
- **OpenAPI Schema**: Available at `/openapi.json` (machine-readable API specification)
"""

APP_METADATA = {
    "title": "NVIDIA Orchestrator",
    "description": APP_DESCRIPTION,
    "version": "1.0.0",
    "contact": {
        "name": "NVIDIA Cloud Platform",
    },
    "license_info": {
        "name": "Proprietary",
    },
}

