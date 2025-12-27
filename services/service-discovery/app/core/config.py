"""FastAPI application configuration."""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints for service monitoring",
    },
    {
        "name": "services",
        "description": "Service discovery and health monitoring operations",
    },
]

APP_DESCRIPTION = """
Service Discovery and Health Monitoring Service for NVIDIA Cloud Platform.

This service provides real-time service discovery and health monitoring, providing:

* **Service Discovery**: Real-time cache of healthy containers using Consul Watch API
* **Health Monitoring**: Tracks container health status via Consul
* **Fast Lookup**: In-memory cache for sub-millisecond service lookups
* **App Indexing**: Indexes containers by `app_hostname` for fast routing

## Features

- Consul Watch API integration for real-time updates
- In-memory cache of healthy containers indexed by `image_id` and `app_hostname`
- Kafka event consumption for container lifecycle updates
- Fast lookup API for Load Balancer integration

## Documentation

- **Swagger UI**: Available at `/docs` (interactive API documentation)
- **ReDoc**: Available at `/redoc` (alternative documentation format)
- **OpenAPI Schema**: Available at `/openapi.json` (machine-readable API specification)
"""

APP_METADATA = {
    "title": "NVIDIA Service Discovery",
    "description": APP_DESCRIPTION,
    "version": "1.0.0",
    "contact": {
        "name": "NVIDIA Cloud Platform",
    },
    "license_info": {
        "name": "Proprietary",
    },
}
