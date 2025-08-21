from fastapi import APIRouter
from app.database.config import get_db
import docker
from docker.errors import DockerException
from fastapi import HTTPException

docker_client = docker.from_env()

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db = next(get_db())
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        
        # Check Docker connection
        docker_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "docker": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

