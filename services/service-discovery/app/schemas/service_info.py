from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime 

class ServiceInfo(BaseModel):
    """
    Represents a healthy service from Consul.
    Used in ServiceCache for fast lookups.
    """
    container_id: str = Field(..., description="Docker container ID")
    container_ip: str = Field(..., description="Internal IP address")
    internal_port: int = Field(..., description="Port inside container")
    external_port: Optional[int] = Field(None, description="External port on host")
    status: str = Field(..., description="Health check status: passing/warning/critical")
    tags: List[str] = Field(default_factory=list, description="Service tags from Consul")
    image_id: Optional[int] = Field(None, description="Extracted from tags")
    app_hostname: Optional[str] = Field(None, description="App hostname identifier extracted from tags")
    user_id: Optional[int] = Field(None, description="user id")
    timestamp: Optional[datetime] = Field(default=None,description="Timestamp in UTC")
    class Config:
        json_schema_extra = {
            "example": {
                "container_id": "abc123def456",
                "container_ip": "172.18.0.10",
                "internal_port": 80,
                "external_port": 32768,
                "status": "passing",
                "tags": ["image-1", "app-hostname-example.com", "external-port-32768"],
                "image_id": 1,
                "app_hostname": "example.com"
            }
        }