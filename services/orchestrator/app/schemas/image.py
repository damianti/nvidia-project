from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.schemas.container import ContainerResponse

# Image schemas
class ImageBase(BaseModel):
    name: str
    tag: str
    app_hostname: str
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
    app_hostname: str
    
    class Config:
        from_attributes = True
    

class ImageWithContainers(ImageResponse):
    """ Image with its containers nested"""
    
    containers: List[ContainerResponse] = []  
    
    class Config:
        from_attributes = True