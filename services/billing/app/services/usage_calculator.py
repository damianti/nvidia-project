from datetime import datetime
from app.utils.config import RATE_PER_MINUTE

def calculate_duration_minutes(start_time: datetime, end_time: datetime) -> int:
    delta = end_time - start_time
    return delta.total_seconds() / 60
    

def calculate_cost(duration_minutes: int, rate_per_minute: float) -> float:
    return duration_minutes * RATE_PER_MINUTE