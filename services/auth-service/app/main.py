from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database.models import Base
from .database.config import engine

from app.api import auth
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.config import (
    HOST,
    PORT,
    SERVICE_NAME,
)
logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    logger.info(
        "auth.startup",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    try:
        Base.metadata.create_all(bind=engine)
        
    except Exception as e:
        logger.error(
            "auth.startup.database_error",
            extra={
                "error": str(e),
                "service_name": SERVICE_NAME
            }
        )
        raise
    yield
    
    # Shutdown
    logger.info(
        "auth.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    


    
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA auth-service",
    description="authentication service for cloud services",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA auth-service",
        "version": "1.0.0",
        "endpoints": {
            "POST /auth/login": "Authenticate user",
            "POST /auth/signup": "Register new user",
            "GET /auth/me": "Get current user info",
            "POST /auth/logout": "Logout user",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": SERVICE_NAME}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "auth.run",
        extra={
            "host": HOST,
            "port": PORT,
            "service_name": SERVICE_NAME,
        }
    )
    uvicorn.run(app, host=HOST, port=PORT)


