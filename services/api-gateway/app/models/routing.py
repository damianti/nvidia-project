from enum import Enum
from typing import Optional


class RoutingInfo:
    def __init__(self, target_host, target_port, container_id, image_id, ttl) -> None:
        self.target_host = target_host
        self.target_port = target_port
        self.container_id = container_id
        self.image_id = image_id
        self.ttl = ttl

class LbError(Enum):
    NOT_FOUND = "not found"
    NO_CAPACITY = "no capacity"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RouteResult:
    def __init__(
        self, 
        ok: bool, 
        data: Optional[RoutingInfo] = None, 
        error: Optional[LbError] = None, 
        status_code: Optional[int] = None, 
        message: Optional[str] = None
    ) -> None:
        self.ok = ok
        self.data = data
        self.error = error
        self.status_code = status_code
        self.message = message