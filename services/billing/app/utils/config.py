# Configuration constants
import os

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "billing")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Service URLs
LOAD_BALANCER_URL = os.getenv("LOAD_BALANCER_URL", "http://load-balancer:3004")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:3003")

# Kafka variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "billing")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Constants
RATE_PER_MINUTE = 0.01
