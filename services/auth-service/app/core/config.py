"""FastAPI application configuration."""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints for service monitoring",
    },
    {
        "name": "auth",
        "description": "User authentication and authorization operations",
    },
]

APP_DESCRIPTION = """
Authentication Service for NVIDIA Cloud Platform.

This service handles user authentication and authorization, providing:

* **User Registration**: Create new user accounts with email and password
* **User Login**: Authenticate users and issue JWT tokens
* **User Logout**: Invalidate user sessions
* **User Info**: Retrieve current authenticated user information

## Authentication

All operations use JWT (JSON Web Tokens) for authentication. Tokens are:
- Set as HttpOnly cookies for web clients (secure by default)
- Valid for 1 hour by default
- Required for protected endpoints

## Documentation

- **Swagger UI**: Available at `/docs` (interactive API documentation)
- **ReDoc**: Available at `/redoc` (alternative documentation format)
- **OpenAPI Schema**: Available at `/openapi.json` (machine-readable API specification)
"""

APP_METADATA = {
    "title": "NVIDIA Auth Service",
    "description": APP_DESCRIPTION,
    "version": "1.0.0",
    "contact": {
        "name": "NVIDIA Cloud Platform",
    },
    "license_info": {
        "name": "Proprietary",
    },
}

