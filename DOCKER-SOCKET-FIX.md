# Docker Socket Access Fix

## Problem
The Orchestrator container cannot access the Docker daemon on the host, resulting in the error:
```
docker.errors.DockerException: Error while fetching server API version: Not supported URL scheme http+docker
```

## Root Cause
The container runs as user `appuser` (ID 1000) but the Docker socket belongs to `root` (ID 0), causing permission issues.

## Solution Applied
Added `user: "0:0"` to the orchestrator service in `docker-compose.yml` to run the container as root, which has access to the Docker socket.

## Configuration
```yaml
orchestrator:
  build:
    context: ./teams/team3-orchestrator
    dockerfile: Dockerfile
  container_name: nvidia-orchestrator
  user: "0:0"  # Run as root to access Docker socket
  environment:
    - DATABASE_URL=postgresql://nvidia_user:nvidia_password@postgres:5432/nvidia_cloud
    # ... rest of configuration
```

## Alternative Solutions (Not Applied)
1. **Socket Permissions**: Change volume mount to `/var/run/docker.sock:/var/run/docker.sock:rw`
2. **User Group**: Add the container user to the docker group (more complex)

## Security Note
Running as root is less secure but necessary for Docker-in-Docker scenarios. In production, consider using Docker-in-Docker (DinD) or a dedicated Docker API service.

## Date Applied
October 21, 2025

## Status
✅ Applied and working
