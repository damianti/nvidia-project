"""FastAPI application configuration."""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints for service monitoring",
    },
    {
        "name": "auth",
        "description": "User authentication and authorization operations. All requests are proxied to the auth-service.",
    },
    {
        "name": "proxy",
        "description": "Request routing and API proxying operations. Routes user application requests and proxies Orchestrator API calls.",
    },
]

APP_DESCRIPTION = """
API Gateway for NVIDIA Cloud Platform.

This service acts as the single entry point for all API requests, providing:

* **Authentication**: User login, signup, logout, and user info (proxied to auth-service)
* **Container Routing**: Routes HTTP requests to user applications via Load Balancer
* **Orchestrator Proxy**: Proxies authenticated API requests for container and image management
* **Caching**: Maintains routing cache with automatic cleanup for improved performance

## Authentication

Most endpoints require authentication via JWT token. The token is automatically sent via:
- HttpOnly cookie (preferred for web clients)
- Authorization header: `Bearer <token>` (for API clients)

## Documentation

- **Swagger UI**: Available at `/docs` (interactive API documentation)
- **ReDoc**: Available at `/redoc` (alternative documentation format)
- **OpenAPI Schema**: Available at `/openapi.json` (machine-readable API specification)
"""

APP_METADATA = {
    "title": "NVIDIA API Gateway",
    "description": APP_DESCRIPTION,
    "version": "1.0.0",
    "contact": {
        "name": "NVIDIA Cloud Platform",
    },
    "license_info": {
        "name": "Proprietary",
    },
}
