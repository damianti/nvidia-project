from pydantic import  BaseModel
from datetime import datetime



# Container schemas
class ContainerBase(BaseModel):
    name: str
    port: int
    status: str = "running"
    cpu_usage: str = "0.0"
    memory_usage: str = "0m"

class ContainerCreate(ContainerBase):
    image_id: int
    count: int = 1  

class ContainerResponse(ContainerBase):
    id: int
    container_id: str
    created_at: datetime
    image_id: int
    user_id: int
    
    class Config:
        from_attributes = True 
