import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ContainerData:

    def __init__(self,container_id: str, image_id: int, external_port: int, status: str = "running")-> None:
        self.container_id = container_id
        self.image_id = image_id
        self.external_port = external_port
        self.status = status

# TODO: implement a more complex way to choose the container (for example, free memory)
class ContainerPool:
    
    def __init__(self) -> None:
        self.pool = {}

    def find_container(self, image_id: int, container_id: str) -> Optional[ContainerData]:
        """lo por image_id y container_id"""
        if not self.pool.get(image_id):
            return None
        
        containers = self.pool[image_id]["containers"]
        for container in containers:
            if container.container_id == container_id:
                return container
        
        return None 

    def add_container(self, container: ContainerData)-> None:
        if self.pool.get(container.image_id) is None:
            self.pool[container.image_id] = {
                "containers": [], 
                "round_robin_index": 0
                }

        self.pool[container.image_id]["containers"].append(container)
        logger.info(f"Added container {container.container_id} to pool for image {container.image_id}")

    def remove_container(self, image_id: int, container_id: str) -> bool:
        """Remover un container del pool por image_id y container_id"""
        if not self.pool.get(image_id):
            logger.warning(f"Image {image_id} not found in pool")
            return False
        
        containers = self.pool[image_id]["containers"]
        for i, container in enumerate(containers):
            if container.container_id == container_id:
                containers.pop(i)
                logger.info(f"Removed container {container_id} from pool for image {image_id}")
                return True
        
        logger.warning(f"Container {container_id} not found for image {image_id}")
        return False
        
    
    def get_next_container(self, image_id: int) -> Optional[ContainerData]: 
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

        return {
            image_id: {
                "count": len(data["containers"]),
                "containers": [c.container_id for c in data["containers"]],
                "round_robin_index": data["round_robin_index"]
            }
            for image_id, data in self.pool.items()
        }