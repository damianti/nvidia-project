import threading
from typing import Optional
from datetime import datetime



class CacheEntry:
    def __init__(self, target_host: str, target_port: str, container_id: str, image_id: int, expires_at: datetime) -> None:
        self.target_host = target_host
        self.target_port = target_port
        self.container_id = container_id
        self.image_id = image_id
        self.expires_at = expires_at
        
    
    def expiration(self):
        return self.expires_at

class Cache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.store: dict[tuple[str, str], CacheEntry] = {}


    def get(self, website_url: str, client_ip: str)-> Optional[CacheEntry]:
        with self._lock:
            if (website_url, client_ip) not in self.store:
                return None

            
            if self.store[(website_url, client_ip)].expiration() <= datetime.now():
                self.store.pop((website_url, client_ip))
                return None

            return self.store[(website_url, client_ip)]

    def set(self,  website_url: str, client_ip: str, entry: CacheEntry) -> None:
        with self._lock:
            self.store[(website_url, client_ip)] = entry

    def invalidate(self, website_url: str, client_ip: str):
        with self._lock:
            self.store.pop((website_url, client_ip))

    def clear_expired(self)-> int:
        """ 
        Clean expired entries from cache
        Returns: Number of removed entries
        """
        now = datetime.now()
        removed = 0
        with self._lock:
            expired_keys = []
            for key, entry in self.store.items():
                if entry.expires_at <= now:
                    expired_keys.append(key)

            for key in expired_keys:
                self.store.pop(key)
                removed += 1
        
        return removed