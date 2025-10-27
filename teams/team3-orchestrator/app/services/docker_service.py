import docker
import os
from fastapi import HTTPException
from docker.errors import DockerException
from docker.models.containers import Container

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

def run_container(image_name: str, image_tag: str , container_name: str, env_vars: dict ) -> Container:
    try:
        
        try: 
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cannot connect to docker DinD. Error: {str(e)}"
            )
        container = client.containers.run(
            image= f"{image_name}:{image_tag}",
            name= container_name, 
            ports={'80/tcp': None},
            detach=True,
            environment = env_vars or {}
            )
        container.reload()
        port_bindings = container.attrs['NetworkSettings']['Ports']
        external_port = int(port_bindings['80/tcp'][0]['HostPort']) if port_bindings.get('80/tcp') else None

        return container, external_port

    except DockerException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Docker container run failed: {str(e)}") 

def start_container(container_docker_id: str) -> Container:
    """"Start an existing container """
    try:
        client = docker.from_env()
        container = client.containers.get(container_docker_id)
        container.start()
        return container
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
    
    