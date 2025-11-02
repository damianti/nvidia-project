import logging
import threading
from typing import Optional, List


logger = logging.getLogger("load-balancer")


class ContainerData:

    def __init__(self, container_id: str, image_id: int, external_port: int, status: str = "running", container_name: str = None)-> None:
        self.container_id = container_id
        self.image_id = image_id
        self.external_port = external_port  # Por compatibilidad, pero usaremos el puerto interno 80
        self.status = status
        self.container_name = container_name or container_id  # Nombre del container para usar como hostname
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
        logger.info(f"Added container {container.container_id} to pool for image {container.image_id}")

    def remove_container(self, image_id: int, container_id: str) -> bool:
        with self._lock:
            if not self.pool.get(image_id):
                logger.warning(f"Image {image_id} not found in pool")
                return False
            
            containers = self.pool[image_id]["containers"]
            for i, container in enumerate(containers):
                if container.container_id == container_id:
                    containers.pop(i)
                    
                    if not containers:
                        del self.pool[image_id]
                    else:
                        self.pool[image_id]["round_robin_index"] %= max(1, len(containers))
                    logger.info(f"Removed container {container_id} from pool for image {image_id}")
                    
                    return True
            
        logger.warning(f"Container {container_id} not found for image {image_id}")
        return False
        
    
    def get_next_container(self, image_id: int) -> Optional[ContainerData]: 
        with self._lock:
            if not self.pool.get(image_id):
                logger.warning(f"No containers found for image {image_id}")
                return None
            
            containers = self.pool[image_id]["containers"]
            if not containers:
                logger.warning(f"No containers available for image {image_id}")
                return None

            index = self.pool[image_id]["round_robin_index"]
            containers_checked = 0
            total_containers = len(containers)
        
            while containers_checked < total_containers:
                selected = containers[index]
                
                if selected.status == "running":
                    self.pool[image_id]["round_robin_index"] = (index+1) % total_containers
                    logger.info(f"Selected container {selected.container_id} for image {image_id}")    
                    return selected
                
                index = (index+1) % total_containers
                containers_checked +=1

        logger.warning(f"No running containers for image {image_id}")
        return None

        
    def start_container(self, image_id: int, container_id: str)-> bool:
        with self._lock:
            if not self.pool.get(image_id):
                return False
        
            containers = self.pool[image_id]["containers"]

            for container in containers:
                if container.container_id == container_id:
                    container.status = "running"
                    logger.info(f"Started container {container_id} for image {image_id}")
                    return True
            
        logger.warning(f"Container {container_id} not found for image {image_id}")
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
                    logger.info(f"Stopped container {container_id} for image {image_id}")
                    return True
            
        logger.warning(f"Container {container_id} not found for image {image_id}")
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