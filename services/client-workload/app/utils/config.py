import os

SERVICE_NAME = "client-workload"

# Service URLs
LOAD_BALANCER_URL = os.getenv("LOAD_BALANCER_URL", "http://load-balancer:3004")
SERVICE_DISCOVERY_URL = os.getenv("SERVICE_DISCOVERY_URL", "http://service-discovery:3006")

# Service port
PORT = int(os.getenv("PORT", "3008"))

