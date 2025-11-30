from datetime import datetime, timezone
from typing import Optional
from app.utils.config import RATE_PER_MINUTE

def calculate_duration_minutes(start_time: datetime, end_time: datetime) -> int:
    """
    Calculate duration in minutes between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp (must be after start_time)
    
    Returns:
        Duration in minutes (rounded to nearest integer)
    
    Raises:
        ValueError: If end_time is before start_time
    """
    if end_time < start_time:
        raise ValueError(f"end_time ({end_time}) must be after start_time ({start_time})")
    
    delta = end_time - start_time
    total_seconds = delta.total_seconds()
    minutes = total_seconds / 60
    
    # Round to nearest integer (you could also use math.ceil() to round up)
    return int(round(minutes))


def calculate_cost(duration_minutes: int, rate_per_minute: float = RATE_PER_MINUTE) -> float:
    """
    Calculate cost based on duration and rate.
    
    Args:
        duration_minutes: Duration in minutes
        rate_per_minute: Rate per minute (defaults to RATE_PER_MINUTE from config)
    
    Returns:
        Total cost (rounded to 2 decimal places)
    """
    if duration_minutes < 0:
        raise ValueError(f"duration_minutes must be >= 0, got {duration_minutes}")
    
    cost = duration_minutes * rate_per_minute
    # Round to 2 decimal places for currency
    return round(cost, 2)


def calculate_estimated_cost(
    start_time: datetime, 
    end_time: Optional[datetime] = None,
    rate_per_minute: float = RATE_PER_MINUTE
) -> float:
    """
    Calculate estimated or final cost based on duration.
    If end_time is None, calculates cost up to current time (estimated cost for active containers).
    If end_time is provided, calculates final cost.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp (None for active containers - uses current time)
        rate_per_minute: Rate per minute (defaults to RATE_PER_MINUTE from config)
    
    Returns:
        Estimated or final cost (rounded to 2 decimal places)
    """
    if end_time is None:
        # Calculate estimated cost for active container (up to now)
        end_time = datetime.now(timezone.utc)
    
    if end_time < start_time:
        raise ValueError(f"end_time ({end_time}) must be after start_time ({start_time})")
    
    duration_minutes = calculate_duration_minutes(start_time, end_time)
    return calculate_cost(duration_minutes, rate_per_minute)