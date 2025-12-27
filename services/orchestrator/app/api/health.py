from fastapi import APIRouter, HTTPException
from app.database.config import get_db
import docker

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="Health check",
    description="Detailed health check endpoint that verifies database and Docker connectivity.",
    response_description="Service health status with dependency checks",
    responses={
        200: {
            "description": "Service health status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "docker": "connected",
                    }
                }
            },
        }
    },
)
async def health_check():
    """
    Detailed health check endpoint.

    Checks the health of the service and its dependencies:
    - Database connectivity (PostgreSQL)
    - Docker daemon connectivity

    Returns:
        dict: Health status with database and Docker connection status
    """
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

    return {"status": "healthy", "database": db_status, "docker": docker_status}


@router.get("/docker-diagnostics")
async def docker_diagnostics():
    """Ejecuta diagnósticos completos de Docker"""
    try:
        from app.services.docker_diagnostics import (
            check_docker_socket,
            check_docker_env,
            test_docker_connection_methods,
            check_current_user,
        )

        return {
            "user_info": check_current_user(),
            "socket_info": check_docker_socket(),
            "environment": check_docker_env(),
            "connection_tests": test_docker_connection_methods(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error ejecutando diagnósticos: {str(e)}"
        )
