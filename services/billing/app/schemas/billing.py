from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List

class BillingSummaryResponse(BaseModel):
    image_id: int
    container_id: int
    start_time: datetime
    end_time: datetime
    duration: timedelta
    cost: float


class BillingDetailResponse(BaseModel):
