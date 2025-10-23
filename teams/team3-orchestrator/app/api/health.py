from fastapi import APIRouter
from app.database.config import get_db
import docker
from docker.errors import DockerException
from fastapi import HTTPException


router = APIRouter(tags=["health"])

@router.get("/")
async def health_check():
    """Detailed health check"""
    try:
        db = next(get_db())
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as db_error:
        db_status = f"disconnected: {str(db_error)}"
    
    try:
        # Check Docker connection
        docker_client = docker.from_env()
        docker_client.ping()
        docker_status = "connected"
    except Exception as docker_error:
        docker_status = f"disconnected: {str(docker_error)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "docker": docker_status
    }


@router.get("/docker-diagnostics")
async def docker_diagnostics():
    """Ejecuta diagnósticos completos de Docker"""
    try:
        from app.services.docker_diagnostics import (
            check_docker_socket,
            check_docker_env,
            test_docker_connection_methods,
            check_current_user
        )
        
        return {
            "user_info": check_current_user(),
            "socket_info": check_docker_socket(),
            "environment": check_docker_env(),
            "connection_tests": test_docker_connection_methods()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando diagnósticos: {str(e)}"
        )

