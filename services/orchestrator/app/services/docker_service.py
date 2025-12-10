import docker
import os
from fastapi import HTTPException
import logging
from docker.errors import DockerException
from docker.models.containers import Container
from typing import Optional

logger = logging.getLogger("orchestrator")

def generate_html(folder: str, website_url: str) -> None:
    html_content = f'''<!DOCTYPE html>
                <html>
                <head>
                    <meta http-equiv="refresh" content="0; url={website_url}">
                    <title>Redirecting...</title>
                </head>
                <body>
                    <p>Redirecting to your website...</p>
                </body>
                </html>'''
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

def build_image(image_name: str, image_tag: str, website_url: str, user_id: int) -> None:
    
    folder = f"./builds/{user_id}"
    os.makedirs(folder, exist_ok=True)
    try:
    
        generate_html(folder, website_url)
        generate_dockerfile(folder)
        
        try: 
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cannot connect to docker DinD. Error: {str(e)}"
            )
        client.images.build(
            path=folder,
            tag=f"{image_name}:{image_tag}")
    
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
            

def cleanup_files(folder: str)-> None:
    if os.path.exists(f"{folder}/index.html"):
        os.remove(f"{folder}/index.html")
    if os.path.exists(f"{folder}/Dockerfile"):
        os.remove(f"{folder}/Dockerfile")
    if os.path.exists(folder):
        os.rmdir(folder)

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
        # NOTE: The containers are created inside docker-dind, which has its own network context.
        # The nvidia-network exists on the Docker Compose host, not inside docker-dind.
        # Therefore, we cannot connect the containers directly to nvidia-network from here.
        # Solution: Create the container WITHOUT specifying a network, and then expose port 80.
        # The container will be accessible from docker-dind using the exposed port.
        
        # Create container with dynamically exposed port (not fixed)
        # This allows the container to be accessible from other containers in docker-dind
        container = client.containers.run(
            image=f"{image_name}:{image_tag}",
            name=container_name,
            ports={'80/tcp': None},  # Expose port 80 dynamically
            detach=True,
            environment=env_vars or {}
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
                container.stop()
                container.remove()
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
                container.stop()
                container.remove()
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
        container.start()
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
        container.stop()
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
        container.remove()
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
    
    