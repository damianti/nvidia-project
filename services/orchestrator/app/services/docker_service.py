import docker
import os
from fastapi import HTTPException
import logging
from docker.errors import DockerException, APIError
from docker.models.containers import Container
from typing import Optional, TypeVar, Callable
import time

RETRYABLE_HTTP_STATUS_CODES = {
    409,  # Conflict: port/name already in use
    500,  # Internal Server Error: Docker daemon error
}
logger = logging.getLogger("orchestrator")

def generate_html(folder: str, app_hostname: str) -> None:
    html_content = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{app_hostname}</title>
  </head>
  <body>
    <h1>Deployed app: {app_hostname}</h1>
    <p>This is a placeholder image. Next step: build from uploaded source.</p>
  </body>
</html>
"""
    with open (f"{folder}/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_dockerfile(folder: str) -> None:
    
    base_image = "nginx:alpine"
    port = 80

    dockerfile_content = f"""
    FROM {base_image}
    COPY index.html /usr/share/nginx/html/
    EXPOSE {port}
    """
    
    with open (f"{folder}/Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)

def build_image(image_name: str, image_tag: str, app_hostname: str, user_id: int) -> None:
    
    folder = f"./builds/{user_id}"
    os.makedirs(folder, exist_ok=True)
    try:
    
        generate_html(folder, app_hostname)
        generate_dockerfile(folder)
        
        try: 
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cannot connect to docker DinD. Error: {str(e)}"
            )
        _retry_docker_operation(
            lambda:
                client.images.build(
                    path=folder,
                    tag=f"{image_name}:{image_tag}")
        )
        cleanup_files(folder)

    except DockerException as e:
        cleanup_files(folder)
        raise HTTPException(
            status_code=500,
            detail=f"Docker build failed: {str(e)}")
    except OSError as e:
        cleanup_files(folder)
        raise HTTPException(
            status_code=500,
            detail=f"File system error: {str(e)}")

    except Exception as e:
        cleanup_files(folder)
        raise HTTPException(
            status_code=500,
            detail=f"unexpected error: {str(e)}")
            

def cleanup_files(folder: str) -> None:
    if os.path.exists(f"{folder}/index.html"):
        os.remove(f"{folder}/index.html")
    if os.path.exists(f"{folder}/Dockerfile"):
        os.remove(f"{folder}/Dockerfile")
    if os.path.exists(folder):
        os.rmdir(folder)
    
def _is_retryable_error(error) -> bool:
    if not isinstance(error, APIError):
        return False
    try:
        status_code = error.response.status_code
        return status_code in RETRYABLE_HTTP_STATUS_CODES
    
    except (AttributeError, KeyError):
        return True

T = TypeVar('T')
def _retry_docker_operation(
    operation: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0
    ) -> T:
    attempt = 1
    delay = initial_delay
    while attempt <= max_retries:
        try:
            result = operation()
            if attempt > 1:
                logger.info(
                    "docker.operation.retry_succeeded",
                    extra={
                        "attempt": attempt,
                        "max_retries": max_retries
                    }
                )
            return result
        except Exception as e :
            if _is_retryable_error(e):
                logger.warning(
                    "docker.operation.retry_attempt",
                    extra={
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "retry_delay_seconds": delay
                    }
                )
                if attempt >= max_retries:
                    logger.error(
                        "docker.operation.retry_exhausted",
                        extra={
                            "attempt": attempt,
                            "max_retries": max_retries,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    raise e
                time.sleep(delay)
                delay*=2
                attempt+=1
            else:
                logger.error(
                    "docker.operation.non_retryable_error",
                    extra={
                        "attempt": attempt,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise e


    



def get_external_port(container: Container) -> Optional[int]:
    """
    Extract the external port (HostPort) from a container's port bindings.
    
    Args:
        container: Docker Container object (should have reload() called before this)
    
    Returns:
        External port number if found, None otherwise
    """
    try:
        network_settings = container.attrs.get('NetworkSettings', {})
        port_bindings = network_settings.get('Ports', {})
        
        # Look for port 80/tcp binding
        port_80_binding = port_bindings.get('80/tcp')
        if port_80_binding and len(port_80_binding) > 0:
            host_port = port_80_binding[0].get('HostPort')
            if host_port:
                return int(host_port)
        
        return None
    except (KeyError, ValueError, IndexError, AttributeError) as e:
        logger.warning(
            "docker.port_extraction.error",
            extra={
                "container_id": container.id,
                "container_name": container.name,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        return None


def get_container_ip_from_container(container: Container) -> Optional[str]:
    """
    Extract the internal IP address from a container's network settings.
    
    Args:
        container: Docker Container object (should have reload() called before this)
    
    Returns:
        IP address string if found, None otherwise
    """
    try:
        network_settings = container.attrs.get('NetworkSettings', {})
        
        # Try to get IP from the first network
        networks = network_settings.get('Networks', {})
        if networks:
            for network_name, network_info in networks.items():
                ip_address = network_info.get('IPAddress')
                if ip_address:
                    return ip_address
        
        # Fallback to IPAddress field (default bridge network)
        ip_address = network_settings.get('IPAddress')
        if ip_address:
            return ip_address
        
        return None
    except (KeyError, AttributeError) as e:
        logger.warning(
            "docker.ip_extraction.error",
            extra={
                "container_id": container.id,
                "container_name": container.name,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        return None

def run_container(image_name: str, image_tag: str , container_name: str, env_vars: dict ) -> tuple[Container, int, str]:
    """
    Creates and runs a container, connecting it directly to the nvidia-network.
    The containers do not expose ports publicly (they are only accessible from the Docker network).
    Returns: (container, external_port, container_ip)
    """
    try:
        
        try: 
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cannot connect to docker DinD. Error: {str(e)}"
            )
        
        
        container = _retry_docker_operation(
            lambda:
                client.containers.run(
                    image=f"{image_name}:{image_tag}",
                    name=container_name,
                    ports={'80/tcp': None},  # Expose port 80 dynamically
                    detach=True,
                    environment=env_vars or {}
                )
        )
        container.reload()
        
        # Extract external port and IP using helper functions
        external_port = get_external_port(container)
        if external_port is None:
            try:
                logger.error(
                    "docker.port_extraction.failed",
                    extra={
                        "container_name": container_name,
                        "container_id": container.id
                    }
                )
                try:
                    _retry_docker_operation(lambda: container.stop())
                except Exception:
                    pass  # Ignore stop failures in cleanup
                try:
                    _retry_docker_operation(lambda: container.remove())
                except Exception:
                    pass  # Ignore remove failures in cleanup
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Failed to assign external port to container '{container_name}'."
            )
        
        container_ip = get_container_ip_from_container(container)
        if not container_ip:
            try:
                logger.error(
                    "docker.ip_extraction.failed",
                    extra={
                        "container_name": container_name,
                        "container_id": container.id
                    }
                )
                try:
                    _retry_docker_operation(lambda: container.stop())
                except Exception:
                    pass  # Ignore stop failures in cleanup
                try:
                    _retry_docker_operation(lambda: container.remove())
                except Exception:
                    pass  # Ignore remove failures in cleanup
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Could not obtain IP address for container '{container_name}'"
            )
        
        return container, external_port, container_ip

    except DockerException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Docker container run failed: {str(e)}") 

def start_container(container_docker_id: str) -> tuple[Container, int, str]:
    """
    Start an existing container and return updated port and IP information.
    
    Args:
        container_docker_id: Docker container ID
    
    Returns:
        Tuple of (container, external_port, container_ip)
    """
    try:
        client = docker.from_env()
        container = client.containers.get(container_docker_id)
        _retry_docker_operation(
            lambda: container.start()
        )
        container.reload()
        
        # Extract external port and IP using helper functions
        external_port = get_external_port(container)
        if external_port is None:
            logger.warning(
                "docker.start.port_extraction.failed",
                extra={
                    "container_id": container_docker_id,
                    "container_name": container.name
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get external port for container '{container_docker_id}' after start."
            )
        
        container_ip = get_container_ip_from_container(container)
        if not container_ip:
            logger.warning(
                "docker.start.ip_extraction.failed",
                extra={
                    "container_id": container_docker_id,
                    "container_name": container.name
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get IP address for container '{container_docker_id}' after start."
            )
        
        return container, external_port, container_ip
    except DockerException as e:
        raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}")
    
def stop_container(container_docker_id: str)-> Container:
    """"Stop an existing container """
    try:
        client = docker.from_env()
        container = client.containers.get(container_docker_id)
        _retry_docker_operation(
            lambda: container.stop()
        )
        return container
    except DockerException as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")

def delete_container(container_docker_id: str) -> bool:
    """"remove an existing container """
    try:
        client = docker.from_env()
        container = client.containers.get(container_docker_id)
        
        try:
            container.stop()
        except:
            pass
        _retry_docker_operation(
            lambda: container.remove()
        )
        return True

    except DockerException as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")

def get_container_ip(container_docker_id: str) -> str:
    """Get the internal IP address of a container"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_docker_id)
        container.reload()
        
        # Get IP from NetworkSettings
        network_settings = container.attrs['NetworkSettings']
        
        # Try to get IP from the first network
        if network_settings.get('Networks'):
            for network_name, network_info in network_settings['Networks'].items():
                ip_address = network_info.get('IPAddress')
                if ip_address:
                    return ip_address
        
        # Fallback to IPAddress field (default bridge network)
        ip_address = network_settings.get('IPAddress')
        if ip_address:
            return ip_address
        
        raise HTTPException(
            status_code=500,
            detail=f"Could not find IP address for container '{container_docker_id}'"
        )
    
    except DockerException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container IP: {str(e)}"
        )
    
    