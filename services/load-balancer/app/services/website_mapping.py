import threading



class WebsiteMapping:
    def __init__(self) -> None:
        self.mp = {}
        self._lock = threading.RLock()

    def add(self, website_url: str, image_id: int) -> None:
        key = (website_url or "").strip().lower()
        if not key:
            return
        with self._lock:
            # Mapear a un único image_id (último gana) o mantener set/list si lo prefieres
            self.mp[key] = image_id
    def remove_image(self, website_url: str, image_id: int)-> None:
        key = (website_url or "").strip().lower()
        if not key:
            return
        with self._lock:
            current = self.mp.get(key)
            if current == image_id:
                del self.mp[key]

    def get_image_id(self, website_url: str):
        key = (website_url or "").strip().lower()
        if not key:
            return None
        with self._lock:
            return self.mp.get(key)
    