from fastapi import APIRouter

router = APIRouter(tags=["load_balancer"])

@router.get("/", summary="Health check endpoint")
async def health():
    """Check if the Load Balancer service is healthy and operational"""
    return {"status": "ok"}

