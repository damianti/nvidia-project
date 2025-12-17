# Configuration constants
import os

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
SERVICE_NAME = "orchestrator"
DATABASE_URL = os.getenv("DATABASE_URL")
# Service URLs
LOAD_BALANCER_URL = os.getenv("LOAD_BALANCER_URL", "http://load-balancer:3004")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:3003")


# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
DEFAULT_BUILD_CONTEXT_BASE_DIR = os.getenv("BUILD_CONTEXT_BASE_DIR", "/tmp/orchestrator-sources")
