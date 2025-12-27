from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ImageUploadResponse(BaseModel):
    """Response model for image upload endpoint"""

    id: int
    name: str
    tag: str
    app_hostname: str
    container_port: int
    min_instances: int
    max_instances: int
    cpu_limit: str
    memory_limit: str
    status: str
    created_at: datetime
    user_id: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "myapp",
                "tag": "latest",
                "app_hostname": "myapp.localhost",
                "container_port": 8080,
                "min_instances": 1,
                "max_instances": 3,
                "cpu_limit": "0.5",
                "memory_limit": "512m",
                "status": "building",
                "created_at": "2024-01-01T00:00:00Z",
                "user_id": 1,
            }
        }
    )


class ProxyErrorResponse(BaseModel):
    """Error response for proxy endpoints"""

    detail: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Invalid app hostname"},
                {"detail": "Application not found or no containers available"},
                {"detail": "Authentication required"},
                {"detail": "Resource not found"},
                {"detail": "Internal server error"},
            ]
        }
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response"""

    detail: str | list[dict]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Invalid file format. Expected zip, tar, tar.gz, or tgz"},
                {
                    "detail": [
                        {
                            "loc": ["body", "name"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                },
            ]
        }
    )
