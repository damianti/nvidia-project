from pydantic import BaseModel, Field
from typing import Optional, Literal




class ContainerEventData(BaseModel):
    """
    Data structure for container lifecycle events from Kafka.
    Validates incoming messages and provides type safety.
    """
    event: Literal["container.created", "container.started", "container.stopped", "container.deleted"]
    container_id: str = Field (..., description="Docker container ID")
    container_name: str = Field(..., description="Human-readable container name")
    container_ip: str = Field(..., description="Internal IP address of the container")
    image_id: int = Field(..., description="Database ID of the image", gt=0)
    internal_port: int = Field(..., description="Port exposed inside container", ge=1, le=65535)
    port: int = Field(..., description="External port mapped on host", ge=1, le=65535)
    website_url: Optional[str] = Field(None, description="Website URL for routing")

    class Config:

        json_schema_extra = {
            "example": {
                "event": "container.created",
                "container_id": "abc123def456",
                "container_name": "my-webapp-1",
                "container_ip": "172.18.0.10",
                "image_id": 1,
                "internal_port": 80,
                "port": 32768,
                "website_url": "myapp.nvidia.com"
            }
        }