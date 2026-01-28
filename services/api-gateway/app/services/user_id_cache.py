import threading
from typing import Optional


class UserIdCache:
    """Thread-safe cache for app_hostname -> user_id mapping."""

    def __init__(self):
        self._lock = threading.RLock()
        self.store: dict[str, int] = {}  # app_hostname -> user_id

    def get(self, app_hostname: str) -> Optional[int]:
        """Get user_id for app_hostname, returns None if not found."""
        with self._lock:
            return self.store.get(app_hostname)

    def set(self, app_hostname: str, user_id: int) -> None:
        """Store user_id for app_hostname."""
        with self._lock:
            self.store[app_hostname] = user_id

    def remove(self, app_hostname: str) -> None:
        """Remove mapping (e.g., when image is deleted)."""
        with self._lock:
            self.store.pop(app_hostname, None)
