from pydantic import  BaseModel
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
    count: int = 1
    

class ContainerResponse(ContainerBase):
    id: int
    container_id: str
    external_port: Optional[int]
    created_at: datetime
    image_id: int
    user_id: int
    
    class Config:
        from_attributes = True 
