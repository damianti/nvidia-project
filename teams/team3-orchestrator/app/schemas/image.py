from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Image schemas
class ImageBase(BaseModel):
    name: str
    tag: str
    min_instances: int = 1
    max_instances: int = 3
    cpu_limit: str = "0.5"
    memory_limit: str = "512m"

class ImageCreate(ImageBase):
    user_id: int

class ImageResponse(ImageBase):
    id: int
    status: str
    created_at: datetime
    user_id: int
    
    class Config:
        from_attributes = True

# Container schemas
class ContainerBase(BaseModel):
    name: str
    port: int
    status: str = "running"
    cpu_usage: str = "0.0"
    memory_usage: str = "0m"

class ContainerCreate(BaseModel):
    count: int = 1

class ContainerResponse(ContainerBase):
    id: int
    container_id: str
    created_at: datetime
    image_id: int
    
    class Config:
        from_attributes = True 