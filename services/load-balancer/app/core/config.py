"""FastAPI application configuration."""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints for service monitoring",
    },
    {
        "name": "load_balancer",
        "description": "Load balancing and request routing operations",
    },
]

APP_DESCRIPTION = """
Load Balancer Service for NVIDIA Cloud Platform.

This service provides intelligent request routing and load balancing, providing:

* **Request Routing**: Route HTTP requests to healthy container instances
* **Round Robin**: Distribute requests evenly across available containers
* **Circuit Breaker**: Prevent cascading failures with circuit breaker pattern
* **Fallback Cache**: Serve cached responses when services are unavailable
* **Health Monitoring**: Track service health and availability

## Features

- Round Robin load balancing algorithm
- Circuit Breaker pattern for fault tolerance
- Fallback cache for degraded service handling
- Service Discovery integration for dynamic routing
- Request/response metrics collection

## Documentation

- **Swagger UI**: Available at `/docs` (interactive API documentation)
- **ReDoc**: Available at `/redoc` (alternative documentation format)
- **OpenAPI Schema**: Available at `/openapi.json` (machine-readable API specification)
"""

APP_METADATA = {
    "title": "NVIDIA Load Balancer",
    "description": APP_DESCRIPTION,
    "version": "1.0.0",
    "contact": {
        "name": "NVIDIA Cloud Platform",
    },
    "license_info": {
        "name": "Proprietary",
    },
}

