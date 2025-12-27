"""FastAPI application configuration."""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints for service monitoring",
    },
    {
        "name": "billing",
        "description": "Billing and cost tracking operations",
    },
]

APP_DESCRIPTION = """
Billing and Cost Tracking Service for NVIDIA Cloud Platform.

This service handles automated billing, invoice management, and cost tracking, providing:

* **Billing Summaries**: Aggregated billing information per image
* **Detailed Billing**: Detailed billing with container-level usage records
* **Cost Tracking**: Real-time cost tracking for CPU and memory usage
* **Usage Records**: Historical usage records for containers

## Features

- Automated billing calculation from container usage events
- Kafka event consumption for container lifecycle updates
- Cost aggregation by image and user
- Historical usage tracking
- Detailed billing reports with container-level breakdown

## Documentation

- **Swagger UI**: Available at `/docs` (interactive API documentation)
- **ReDoc**: Available at `/redoc` (alternative documentation format)
- **OpenAPI Schema**: Available at `/openapi.json` (machine-readable API specification)
"""

APP_METADATA = {
    "title": "NVIDIA Billing Service",
    "description": APP_DESCRIPTION,
    "version": "1.0.0",
    "contact": {
        "name": "NVIDIA Cloud Platform",
    },
    "license_info": {
        "name": "Proprietary",
    },
}
