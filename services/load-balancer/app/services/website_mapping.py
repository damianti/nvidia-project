import threading
import logging

from app.utils.config import SERVICE_NAME
logger = logging.getLogger(SERVICE_NAME)


class WebsiteMapping:
    def __init__(self) -> None:
        self.mp = {}
        self._lock = threading.RLock()

    @staticmethod
    def _normalize_key(website_url: str) -> str:
        """Normalize website_url: lowercase, strip, and take out protocol (https://, http://)"""
        if not website_url:
            return ""
        normalized = website_url.strip().lower()
        
        if normalized.startswith("https://"):
            normalized = normalized[8:]
        elif normalized.startswith("http://"):
            normalized = normalized[7:]
        
        normalized = normalized.rstrip("/")
        return normalized

    def add(self, website_url: str, image_id: int) -> None:
        key = self._normalize_key(website_url)
        if not key:
            logger.warning(
                "website_map.empty_after_normalization",
                extra={"original": website_url}
            )
            return
        with self._lock:
            self.mp[key] = image_id
            logger.info(
                "website_map.added",
                extra={
                    "website_url": website_url,
                    "normalized": key,
                    "image_id": image_id,
                }
            )
    
    def remove_image(self, website_url: str, image_id: int) -> None:
        key = self._normalize_key(website_url)
        if not key:
            return
        with self._lock:
            current = self.mp.get(key)
            if current == image_id:
                del self.mp[key]

    def get_image_id(self, website_url: str):
        key = self._normalize_key(website_url)
        if not key:
            logger.warning(
                "website_map.empty_after_normalization",
                extra={"original": website_url}
            )
            return None
        with self._lock:
            image_id = self.mp.get(key)
            if image_id:
                logger.info(
                    "website_map.found",
                    extra={
                        "website_url": website_url,
                        "normalized": key,
                        "image_id": image_id,
                    }
                )
            else:
                logger.warning(
                    "website_map.not_found",
                    extra={
                        "website_url": website_url,
                        "normalized": key,
                        "available_keys": list(self.mp.keys()),
                    }
                )
            return image_id
    