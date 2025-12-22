from pydantic import  BaseModel, Field, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
