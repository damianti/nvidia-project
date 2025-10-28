from fastapi import APIRouter

router = APIRouter(prefix="/images", tags=["images"])

@router.get("/")
def get_images():
    return {"message": "Hello, World!"}


