from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Literal, Optional


class ContainerEventData(BaseModel):
    """
    Data structure for container lifecycle events from Kafka.
    Validates incoming messages and provides type safety.
    """
    event: Literal["container.created", "container.started", "container.stopped", "container.deleted"]
    container_id: str = Field(..., description="Docker container ID")
    container_name: str = Field(..., description="Human-readable container name")
    container_ip: str = Field(..., description="Internal IP address of the container")
    image_id: int = Field(..., description="Database ID of the image", gt=0)
    internal_port: int = Field(..., description="Port exposed inside container", ge=1, le=65535)
    external_port: int = Field(..., description="External port mapped on host", ge=1, le=65535)
    app_hostname: str = Field(..., description="App hostname for routing")
    user_id: Optional[int] = Field(None, description="User ID who owns the container")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp in UTC")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event": "container.created",
                "container_id": "abc123def456",
                "container_name": "my-webapp-1",
                "container_ip": "172.18.0.10",
                "image_id": 1,
                "internal_port": 80,
                "external_port": 32768,
                "app_hostname": "myapp.nvidia.com",
                "user_id": 123,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class UsageRecordResponse(BaseModel):
    """
    Represents a single container usage record.
    Used in detailed billing views.
    """
    id: int
    container_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    cost: Optional[float] = None
    status: str  # "Active" or "Completed"

    model_config = ConfigDict(from_attributes=True)


class BillingSummaryResponse(BaseModel):
    """
    Billing summary for a single image.
    Used in the list endpoint: GET /images
    """
    image_id: int
    total_containers: int = Field(..., description="Total number of containers created for this image")
    total_minutes: int = Field(..., description="Total minutes of usage (sum of all containers)")
    total_cost: float = Field(..., description="Total cost (sum of all containers)")
    active_containers: int = Field(..., description="Number of currently active containers")
    last_activity: Optional[datetime] = Field(None, description="Last container start/stop time")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_id": 456,
                "total_containers": 5,
                "total_minutes": 120,
                "total_cost": 1.20,
                "active_containers": 2,
                "last_activity": "2024-01-15T11:45:00Z"
            }
        }
    )



class BillingDetailResponse(BaseModel):
    """
    Detailed billing information for a specific image.
    Used in the detail endpoint: GET /images/{image_id}
    """
    image_id: int
    summary: BillingSummaryResponse = Field(..., description="Aggregated summary")
    containers: List[UsageRecordResponse] = Field(..., description="List of all container usage records")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_id": 456,
                "summary": {
                    "image_id": 456,
                    "total_containers": 5,
                    "total_minutes": 120,
                    "total_cost": 1.20,
                    "active_containers": 2,
                    "last_activity": "2024-01-15T11:45:00Z"
                },
                "containers": [
                    {
                        "id": 1,
                        "container_id": "abc123",
                        "start_time": "2024-01-15T10:30:00Z",
                        "end_time": "2024-01-15T11:45:00Z",
                        "duration_minutes": 75,
                        "cost": 0.75,
                        "status": "Completed"
                    }
                ]
            }
        }
    )