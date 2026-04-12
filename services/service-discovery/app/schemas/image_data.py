from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ImageEventData(BaseModel):
    """Data structure for image lifecycle events from Kafka."""

    event: str = Field(..., description="Event type, e.g. 'image.deleted'")
    image_id: int = Field(..., description="Database ID of the image", gt=0)
    user_id: Optional[int] = Field(None, description="User ID who owns the image")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp in UTC")
