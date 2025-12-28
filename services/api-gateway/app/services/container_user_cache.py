import threading
from typing import Optional


class ContainerUserCache:
    """Thread-safe cache for container_id -> user_id mapping."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.store: dict[str, int] = {}  # container_id -> user_id
    
    def get(self, container_id: str) -> Optional[int]:
        """Get user_id for container_id, returns None if not found."""
        with self._lock:
            return self.store.get(container_id)
    
    def set(self, container_id: str, user_id: int) -> None:
        """Store user_id for container_id."""
        with self._lock:
            self.store[container_id] = user_id
    
    def remove(self, container_id: str) -> None:
        """Remove mapping (e.g., when container is deleted)."""
        with self._lock:
            self.store.pop(container_id, None)

