import docker
import os
from fastapi import HTTPException
from docker.errors import DockerException
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
                detail=f"No se pudo conectar a DinD. Error: {str(e)}"
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