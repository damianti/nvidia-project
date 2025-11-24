import threading
from typing import Dict, List, Optional

from app.schemas.service_info import ServiceInfo


class RoundRobinSelector:
    """
    Maintains a simple round robin index per image.

    This keeps the load balancer stateless regarding container health,
    relying on service-discovery for the list of running instances.
    """

    def __init__(self) -> None:
        self._indexes: Dict[int, int] = {}
        self._lock = threading.RLock()

    def select(self, image_id: int, services: List[ServiceInfo]) -> Optional[ServiceInfo]:
        if not services:
            return None

        with self._lock:
            current_index = self._indexes.get(image_id, 0)
            selected = services[current_index % len(services)]
            self._indexes[image_id] = (current_index + 1) % len(services)
            return selected

