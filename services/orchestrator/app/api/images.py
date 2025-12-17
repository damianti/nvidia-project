from fastapi import APIRouter
from app.database.config import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List
from fastapi import UploadFile, File, Form


from app.utils.dependencies import get_user_id
from app.schemas.image import ImageCreate, ImageResponse, ImageWithContainers
from app.schemas.container import ContainerResponse
from app.application.services import image_service, container_service

router = APIRouter(tags=["images"])

@router.post("/", response_model=ImageResponse)
async def create_image(
    name: str = Form(...),
    tag: str = Form(...),
    app_hostname: str = Form(...),
    container_port: int = Form(8080),
    min_instances: int = Form(1),
    max_instances: int = Form(3),
    cpu_limit: str = Form("0.5"),
    memory_limit: str = Form("512m"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    data = ImageCreate(
        user_id=user_id,
        name=name,
        tag=tag,
        app_hostname=app_hostname,
        container_port=container_port,
        min_instances=min_instances,
        max_instances=max_instances,
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
    )

    return image_service.create_image_from_upload(
        db=db,
        data=data,
        file=file,
    )


@router.get("/", response_model=List[ImageResponse], summary="List all images")
async def list_images(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """List all registered images"""
    return image_service.get_all_images(db, user_id)



@router.get("/with-containers", response_model=List[ImageWithContainers], summary="List images with their containers")
async def list_images_with_containers(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """List all images with their containers for the current user"""
    return image_service.get_all_images_with_containers(db, user_id)
    


@router.get("/{image_id}", response_model=ImageResponse, summary="Get image details")
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Get a specific image"""
    return image_service.get_image_by_id(db, image_id, user_id)


@router.get("/{image_id}/build-logs", summary="Get build logs for an image")
async def get_image_build_logs(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    image = image_service.get_image_by_id(db, image_id, user_id)
    return {"build_logs": image.build_logs or ""}


@router.get("/{image_id}/containers", response_model=List[ContainerResponse], summary="Get containers for an image")
async def list_image_containers(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """List containers for a specific image"""
    return container_service.get_containers_of_image(db, user_id, image_id)
    

@router.delete("/{image_id}", summary="Delete an image")
async def delete_image(image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Delete an image"""
    image_service.delete_image(db, image_id, user_id)
    return {"message": f"Image {image_id} deleted successfully"}

