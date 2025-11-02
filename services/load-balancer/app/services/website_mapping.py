import threading
import logging

logger = logging.getLogger("api-gateway")


class WebsiteMapping:
    def __init__(self) -> None:
        self.mp = {}
        self._lock = threading.RLock()

    @staticmethod
    def _normalize_key(website_url: str) -> str:
        """Normaliza website_url: lowercase, strip, y quita protocolo (https://, http://)"""
        if not website_url:
            return ""
        normalized = website_url.strip().lower()
        # Quitar protocolo si existe
        if normalized.startswith("https://"):
            normalized = normalized[8:]  # len("https://") = 8
        elif normalized.startswith("http://"):
            normalized = normalized[7:]  # len("http://") = 7
        # Quitar trailing slash opcional
        normalized = normalized.rstrip("/")
        return normalized

    def add(self, website_url: str, image_id: int) -> None:
        key = self._normalize_key(website_url)
        if not key:
            logger.warning(f"Empty website_url after normalization (original: '{website_url}')")
            return
        with self._lock:
            self.mp[key] = image_id
            logger.info(f"Added website_url: '{website_url}' -> normalized: '{key}' -> image_id: {image_id}")
    
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
            logger.warning(f"Empty website_url after normalization (original: '{website_url}')")
            return None
        with self._lock:
            image_id = self.mp.get(key)
            if image_id:
                logger.info(f"Found image_id: {image_id} for website_url: '{website_url}' (normalized: '{key}')")
            else:
                logger.warning(f"Image not found for website_url: '{website_url}' (normalized: '{key}'). Available keys: {list(self.mp.keys())}")
            return image_id
    