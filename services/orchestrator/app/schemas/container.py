from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated
from datetime import datetime
from typing import Optional


# Container schemas
class ContainerBase(BaseModel):
    name: str
    internal_port: int
    status: str = "running"
    cpu_usage: str = "0.0"
    memory_usage: str = "0m"


class ContainerCreate(BaseModel):
    name: str
    image_id: int
    count: Annotated[int, Field(gt=0, lt=10)] = 1


class ContainerResponse(ContainerBase):
    id: int
    container_id: str
    external_port: Optional[int]
    created_at: datetime
    image_id: int
    user_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "myapp-container-1",
                "container_id": "abc123def456",
                "internal_port": 8080,
                "external_port": 30001,
                "status": "running",
                "cpu_usage": "0.5",
                "memory_usage": "256m",
                "created_at": "2024-01-01T00:00:00Z",
                "image_id": 1,
                "user_id": 1
            }
        }
    )
