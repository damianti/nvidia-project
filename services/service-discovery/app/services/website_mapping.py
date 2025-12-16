import threading
import logging

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


class AppHostnameMapping:
    def __init__(self) -> None:
        self.mp = {}
        self._lock = threading.RLock()

    @staticmethod
    def _normalize_key(app_hostname: str) -> str:
        """Normalize app_hostname: lowercase and strip."""
        if not app_hostname:
            return ""
        return app_hostname.strip().lower()

    def add(self, app_hostname: str, image_id: int) -> None:
        key = self._normalize_key(app_hostname)
        if not key:
            logger.warning(
                "app_hostname_map.empty_after_normalization",
                extra={"original": app_hostname},
            )
            return
        with self._lock:
            current = self.mp.get(key)
            if current is not None and current != image_id:
                logger.warning(
                    "app_hostname_map.conflict",
                    extra={
                        "app_hostname": app_hostname,
                        "normalized": key,
                        "existing_image_id": current,
                        "new_image_id": image_id,
                    },
                )
            self.mp[key] = image_id
            logger.info(
                "app_hostname_map.added",
                extra={
                    "app_hostname": app_hostname,
                    "normalized": key,
                    "image_id": image_id,
                },
            )

    def remove_image(self, app_hostname: str, image_id: int) -> None:
        key = self._normalize_key(app_hostname)
        if not key:
            return
        with self._lock:
            current = self.mp.get(key)
            if current == image_id:
                del self.mp[key]

    def get_image_id(self, app_hostname: str):
        key = self._normalize_key(app_hostname)
        if not key:
            logger.warning(
                "app_hostname_map.empty_after_normalization",
                extra={"original": app_hostname},
            )
            return None
        with self._lock:
            image_id = self.mp.get(key)
            if image_id:
                logger.info(
                    "app_hostname_map.found",
                    extra={
                        "app_hostname": app_hostname,
                        "normalized": key,
                        "image_id": image_id,
                    },
                )
            else:
                logger.warning(
                    "app_hostname_map.not_found",
                    extra={
                        "app_hostname": app_hostname,
                        "normalized": key,
                        "available_keys": list(self.mp.keys()),
                    },
                )
            return image_id

    def clear(self) -> None:
        with self._lock:
            self.mp.clear()

    def size(self) -> int:
        with self._lock:
            return len(self.mp)

