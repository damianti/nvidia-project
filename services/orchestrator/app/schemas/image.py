from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import datetime
from typing import List

from app.schemas.container import ContainerResponse


# Image schemas
class ImageBase(BaseModel):
    name: str
    tag: str
    app_hostname: str
    container_port: int = Field(8080, ge=1, le=65535)
    min_instances: int = Field(1, ge=1)
    max_instances: int = Field(3, ge=1)
    cpu_limit: str = "0.5"
    memory_limit: str = "512m"

    @model_validator(mode="after")
    def check_min_le_max(self):
        if self.min_instances > self.max_instances:
            raise ValueError("min_instances must be <= max_instances")
        return self


class ImageCreate(ImageBase):
    user_id: int


class ImageResponse(ImageBase):
    id: int
    status: str
    created_at: datetime
    user_id: int
    app_hostname: str

    model_config = ConfigDict(from_attributes=True)


class ImageWithContainers(ImageResponse):
    """Image with its containers nested"""

    containers: List[ContainerResponse] = []

    model_config = ConfigDict(from_attributes=True)
