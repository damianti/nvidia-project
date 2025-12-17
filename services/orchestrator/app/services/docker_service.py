import docker
from fastapi import HTTPException
import logging
from docker.errors import APIError, BuildError, DockerException
from docker.models.containers import Container
from typing import Iterable, Optional, TypeVar, Callable
import time

RETRYABLE_HTTP_STATUS_CODES = {
    409,  # Conflict: port/name already in use
    500,  # Internal Server Error: Docker daemon error
}
logger = logging.getLogger("orchestrator")

MAX_BUILD_LOG_CHARS = 8000


def _collect_build_logs(logs: Iterable[dict]) -> str:
    lines: list[str] = []
    for chunk in logs:
        if not isinstance(chunk, dict):
            continue
        stream = chunk.get("stream")
        if stream:
            lines.append(str(stream).rstrip())
        error = chunk.get("error")
        if error:
            lines.append(str(error).rstrip())
    return "\n".join(lines)


def build_image_from_context(
    context_dir: str,
    image_name: str,
    image_tag: str,
    dockerfile: str = "Dockerfile",
) -> str:
    try:
        client = docker.from_env()
        client.ping()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot connect to Docker. Error: {str(e)}") from e

    image_ref = f"{image_name}:{image_tag}"
    try:
        _, logs = client.images.build(
            path=context_dir,
            dockerfile=dockerfile,
            tag=image_ref,
            rm=True,
            decode=True,
        )
        return _collect_build_logs(logs)

    except BuildError as e:
        build_log = getattr(e, "build_log", None)
        logs_text = _collect_build_logs(build_log or [])
        if logs_text:
            logs_text = logs_text[-MAX_BUILD_LOG_CHARS:]
        raise HTTPException(
            status_code=500,
            detail=f"Docker build failed for {image_ref}. {logs_text}".strip(),
        ) from e

    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error while building {image_ref}: {str(e)}") from e

    except DockerException as e:
        raise HTTPException(status_code=500, detail=f"Docker error while building {image_ref}: {str(e)}") from e
    
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


    



def get_external_port(container: Container, internal_port: int) -> Optional[int]:
    """
    Extract the external port (HostPort) from a container's port bindings.
    
    Args:
        container: Docker Container object (should have reload() called before this)
        internal_port: Internal TCP port exposed by the container
    
    Returns:
        External port number if found, None otherwise
    """
    try:
        network_settings = container.attrs.get('NetworkSettings', {})
        port_bindings = network_settings.get('Ports', {})
        
        port_key = f"{internal_port}/tcp"
        binding = port_bindings.get(port_key)
        if binding and len(binding) > 0:
            host_port = binding[0].get('HostPort')
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

def run_container(
    image_name: str,
    image_tag: str,
    container_name: str,
    env_vars: dict,
    internal_port: int = 8080,
) -> tuple[Container, int, str]:
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
                    ports={f"{internal_port}/tcp": None},
                    detach=True,
                    environment=env_vars or {}
                )
        )
        container.reload()
        
        # Extract external port and IP using helper functions
        external_port = get_external_port(container, internal_port)
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

def start_container(container_docker_id: str, internal_port: int = 8080) -> tuple[Container, int, str]:
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
        external_port = get_external_port(container, internal_port)
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
    
    