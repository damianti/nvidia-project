import logging
import threading
from typing import Optional, List

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


class ContainerData:

    def __init__(self, container_id: str, image_id: int, external_port: int, status: str = "running", container_name: str = None)-> None:
        self.container_id = container_id
        self.image_id = image_id
        self.external_port = external_port 
        self.status = status
        self.container_name = container_name or container_id  
        self._lock = threading.RLock()

# TODO: implement a more complex way to choose the container (for example, free memory in container)
class ContainerPool:
    
    def __init__(self) -> None:
        self.pool = {}
        self._lock = threading.RLock()


    def find_container(self, image_id: int, container_id: str) -> Optional[ContainerData]:
        with self._lock:
            if not self.pool.get(image_id):
                return None
            
            containers = self.pool[image_id]["containers"]
            for container in containers:
                if container.container_id == container_id:
                    return container
            
        return None 

    def add_container(self, container: ContainerData)-> None:
        with self._lock:
            if self.pool.get(container.image_id) is None:
                self.pool[container.image_id] = {
                    "containers": [], 
                    "round_robin_index": 0
                    }

            self.pool[container.image_id]["containers"].append(container)
        logger.info(
            "pool.container_added",
            extra={
                "container_id": container.container_id,
                "image_id": container.image_id,
            }
        )

    def remove_container(self, image_id: int, container_id: str) -> bool:
        with self._lock:
            if not self.pool.get(image_id):
                logger.warning(
                    "pool.image_not_found",
                    extra={"image_id": image_id}
                )
                return False
            
            containers = self.pool[image_id]["containers"]
            for i, container in enumerate(containers):
                if container.container_id == container_id:
                    containers.pop(i)
                    
                    if not containers:
                        del self.pool[image_id]
                    else:
                        self.pool[image_id]["round_robin_index"] %= max(1, len(containers))
                    logger.info(
                        "pool.container_removed",
                        extra={
                            "container_id": container_id,
                            "image_id": image_id,
                        }
                    )
                    
                    return True
            
        logger.warning(
            "pool.container_not_found",
            extra={
                "container_id": container_id,
                "image_id": image_id,
            }
        )
        return False
        
    
    def get_next_container(self, image_id: int) -> Optional[ContainerData]: 
        with self._lock:
            if not self.pool.get(image_id):
                logger.warning(
                    "pool.no_containers_for_image",
                    extra={"image_id": image_id}
                )
                return None
            
            containers = self.pool[image_id]["containers"]
            if not containers:
                logger.warning(
                    "pool.no_containers_available",
                    extra={"image_id": image_id}
                )
                return None

            index = self.pool[image_id]["round_robin_index"]
            containers_checked = 0
            total_containers = len(containers)
        
            while containers_checked < total_containers:
                selected = containers[index]
                
                if selected.status == "running":
                    self.pool[image_id]["round_robin_index"] = (index+1) % total_containers
                    logger.info(
                        "pool.container_selected",
                        extra={
                            "container_id": selected.container_id,
                            "image_id": image_id,
                        }
                    )
                    return selected
                
                index = (index+1) % total_containers
                containers_checked +=1

        logger.warning(
            "pool.no_running_containers",
            extra={"image_id": image_id}
        )
        return None

        
    def start_container(self, image_id: int, container_id: str)-> bool:
        with self._lock:
            if not self.pool.get(image_id):
                return False
        
            containers = self.pool[image_id]["containers"]

            for container in containers:
                if container.container_id == container_id:
                    container.status = "running"
                    logger.info(
                        "pool.container_started",
                        extra={
                            "container_id": container_id,
                            "image_id": image_id,
                        }
                    )
                    return True
            
        logger.warning(
            "pool.container_not_found",
            extra={
                "container_id": container_id,
                "image_id": image_id,
            }
        )
        return False

    def stop_container(self, image_id: int, container_id: str) -> bool:
        with self._lock:
            if not self.pool.get(image_id):
                return False
            
            containers = self.pool[image_id]["containers"]
            
            # Buscar container por container_id
            for container in containers:
                if container.container_id == container_id:
                    container.status = "stopped"
                    logger.info(
                        "pool.container_stopped",
                        extra={
                            "container_id": container_id,
                            "image_id": image_id,
                        }
                    )
                    return True
            
        logger.warning(
            "pool.container_not_found",
            extra={
                "container_id": container_id,
                "image_id": image_id,
            }
        )
        return False
        

    def get_pool_status(self) -> dict:
        "for debugging - see pool state"
        with self._lock:
            return {
                image_id: {
                    "count": len(data["containers"]),
                    "containers": [c.container_id for c in data["containers"]],
                    "round_robin_index": data["round_robin_index"]
                }
                for image_id, data in self.pool.items()
            }

    def get_containers(self, image_id: int) -> List[str]:
        with self._lock:
            if image_id not in self.pool:
                return []
            return [c.container_id for c in self.pool[image_id]["containers"]]

    def has_containers(self, image_id: int) -> bool:
        with self._lock:
            data = self.pool.get(image_id)
            return bool(data and data["containers"]) 