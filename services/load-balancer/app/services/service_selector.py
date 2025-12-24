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

    def select(
        self, image_id: int, services: List[ServiceInfo]
    ) -> Optional[ServiceInfo]:
        """
        Select the next service using round-robin algorithm.

        Maintains a separate round-robin index for each image_id to ensure
        even distribution across multiple images.

        Args:
            image_id: ID of the image to select a service for
            services: List of available healthy services for this image

        Returns:
            Selected ServiceInfo, or None if services list is empty

        Thread-safe: Uses RLock to prevent race conditions in multi-threaded environments.
        """
        if not services:
            return None

        with self._lock:
            current_index = self._indexes.get(image_id, 0)
            selected = services[current_index % len(services)]
            self._indexes[image_id] = (current_index + 1) % len(services)
            return selected
