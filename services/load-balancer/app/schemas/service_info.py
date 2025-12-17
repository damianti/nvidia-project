from typing import List, Optional

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    container_id: str = Field(..., description="Docker container ID")
    container_ip: str = Field(..., description="Internal IP address")
    internal_port: int = Field(..., description="Port inside container")
    external_port: Optional[int] = Field(
        None, description="External port on host"
    )
    status: str = Field(..., description="Health check status")
    tags: List[str] = Field(default_factory=list, description="Service tags")
    image_id: Optional[int] = Field(None, description="Image identifier")
    app_hostname: Optional[str] = Field(None, description="App hostname tag")

