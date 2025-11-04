# Configuration constants
import os

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
SERVICE_NAME = os.getenv("HOST", "auth-service")
# Service URLs
LOAD_BALANCER_URL = os.getenv("LOAD_BALANCER_URL", "http://load-balancer:3004")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:3003")

# Cache configuration
CACHE_CLEANUP_INTERVAL = int(os.getenv("CACHE_CLEANUP_INTERVAL", "60"))
DEFAULT_CACHE_TTL = int(os.getenv("DEFAULT_CACHE_TTL", "1800"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
