from fastapi import APIRouter, Request, Response, Depends, UploadFile, File, Form

from app.utils.dependencies import (
    get_cached_memory,
    get_lb_client,
    get_orchestrator_client,
    get_http_client,
    get_user_id_cache,
    get_container_user_cache,
    get_metrics_collector,
)
from app.services.user_id_cache import UserIdCache
from app.services.container_user_cache import ContainerUserCache
from app.services.routing_cache import Cache
from app.services.metrics_collector import MetricsCollector
from app.services.routing_cache import Cache
from app.services.gateway_service import handle_route_request, RouteValidationError
from app.services.orchestrator_service import (
    handle_orchestrator_proxy,
    handle_image_upload,
)
from app.utils.dependencies import verify_token_and_get_user_id
from app.schemas.proxy import (
    ImageUploadResponse,
    ProxyErrorResponse,
    ValidationErrorResponse,
)
from app.schemas.user import ErrorResponse

router = APIRouter(tags=["proxy"])


@router.api_route(
    "/apps/{app_hostname}/{remaining_path:path}",
    methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    summary="Route requests to user applications",
    description="""
    Routes HTTP requests to user applications via the Load Balancer.
    
    This endpoint uses path-based routing where:
    - `app_hostname`: The unique identifier for the user's application (e.g., "myapp" or "myapp.example.com")
    - `remaining_path`: The path to forward to the application container (e.g., "/api/users", "/dashboard")
    
    The request is routed to an available container instance using sticky sessions based on client IP.
    
    **Note**: This is a generic proxy endpoint. The response format depends on the target application.
    """,
    responses={
        200: {
            "description": "Request successfully proxied to application",
            "content": {
                "application/json": {
                    "description": "Response from the user's application (format varies)"
                }
            },
        },
        400: {
            "description": "Invalid app_hostname",
            "model": ProxyErrorResponse,
        },
        503: {
            "description": "Application not found or no containers available",
            "model": ProxyErrorResponse,
        },
    },
)
async def apps_route(
    request: Request,
    app_hostname: str,
    remaining_path: str,
    cached_memory: Cache = Depends(get_cached_memory),
    lb_client=Depends(get_lb_client),
    http_client=Depends(get_http_client),
    user_id_cache: UserIdCache = Depends(get_user_id_cache),
    container_user_cache: ContainerUserCache = Depends(get_container_user_cache),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector),
):
    """
    Route HTTP requests to user applications.

    Args:
        request: FastAPI request object
        app_hostname: Application hostname identifier
        remaining_path: Path to forward to the application container
        cached_memory: Routing cache (injected)
        lb_client: Load Balancer client (injected)
        http_client: HTTP client (injected)
        user_id_cache: User ID cache (injected)
        metrics_collector: Metrics collector (injected)

    Returns:
        Response: Proxied response from the application container
    """
    try:
        app_hostname = app_hostname.strip()
        if not app_hostname:
            return Response(content="Invalid app hostname", status_code=400)

        return await handle_route_request(
            request=request,
            app_hostname=app_hostname,
            remaining_path=remaining_path,
            http_client=http_client,
            cached_memory=cached_memory,
            lb_client=lb_client,
            user_id_cache=user_id_cache,
            container_user_cache=container_user_cache,
            metrics_collector=metrics_collector,
        )
    except RouteValidationError as e:
        return Response(content=e.message, status_code=e.status_code)


@router.post(
    "/api/images",
    response_model=ImageUploadResponse,
    status_code=201,
    summary="Upload Docker image",
    description="""
    Upload a Docker image with Dockerfile and build context.
    
    This endpoint accepts a multipart/form-data request containing:
    - A compressed archive (zip, tar, tar.gz, tgz) with the Dockerfile and build context
    - Image metadata (name, tag, app_hostname, etc.)
    
    The image will be built and registered in the system. Requires authentication.
    """,
    responses={
        200: {
            "description": "Image uploaded and built successfully",
            "model": ImageUploadResponse,
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error or invalid file format",
            "model": ValidationErrorResponse,
        },
    },
)
async def upload_image(
    name: str = Form(..., description="Image name (e.g., 'myapp')"),
    tag: str = Form(..., description="Image tag (e.g., 'latest', 'v1.0.0')"),
    app_hostname: str = Form(
        ..., description="Application hostname identifier (e.g., 'myapp.localhost')"
    ),
    container_port: int = Form(
        8080, description="Container port to expose", ge=1, le=65535
    ),
    min_instances: int = Form(
        1, description="Minimum number of container instances", ge=1
    ),
    max_instances: int = Form(
        3, description="Maximum number of container instances", ge=1
    ),
    cpu_limit: str = Form("0.5", description="CPU limit (e.g., '0.5', '1.0', '2')"),
    memory_limit: str = Form(
        "512m", description="Memory limit (e.g., '512m', '1g', '2g')"
    ),
    file: UploadFile = File(
        ...,
        description="Compressed archive (zip, tar, tar.gz, tgz) with Dockerfile and build context",
    ),
    user_id: int = Depends(verify_token_and_get_user_id),
    orchestrator_client=Depends(get_orchestrator_client),
    user_id_cache: UserIdCache = Depends(get_user_id_cache),
):
    """
    Upload Docker image with build context.

    Args:
        name: Image name
        tag: Image tag/version
        app_hostname: Application hostname identifier
        container_port: Port to expose in the container
        min_instances: Minimum number of container instances
        max_instances: Maximum number of container instances
        cpu_limit: CPU resource limit
        memory_limit: Memory resource limit
        file: Compressed archive with Dockerfile and build context
        user_id: Authenticated user ID (from token)
        orchestrator_client: Orchestrator client (injected)
        user_id_cache: User ID cache (injected)

    Returns:
        ImageUploadResponse: Image information including build status
    """
    return await handle_image_upload(
        name=name,
        tag=tag,
        app_hostname=app_hostname,
        container_port=container_port,
        min_instances=min_instances,
        max_instances=max_instances,
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
        file=file,
        user_id=user_id,
        orchestrator_client=orchestrator_client,
        user_id_cache=user_id_cache,
    )


@router.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    summary="Proxy requests to Orchestrator API",
    description="""
    Proxy authenticated API requests to the Orchestrator service.
    
    This endpoint forwards requests to the Orchestrator for container and image management operations.
    All requests require authentication via JWT token.
    
    Examples:
    - `GET /api/images` - List all images
    - `GET /api/images/{id}` - Get image details
    - `POST /api/containers` - Create a container
    - `DELETE /api/containers/{id}` - Delete a container
    
    Note: `/api/images` (POST) has a dedicated endpoint for image uploads with multipart/form-data.
    
    **Note**: This is a generic proxy endpoint. The response format depends on the Orchestrator API endpoint being called.
    """,
    responses={
        200: {
            "description": "Request successfully proxied to Orchestrator",
            "content": {
                "application/json": {
                    "description": "Response from Orchestrator service (format varies by endpoint)"
                }
            },
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
        },
        404: {
            "description": "Resource not found",
            "model": ProxyErrorResponse,
        },
        500: {
            "description": "Internal server error",
            "model": ProxyErrorResponse,
        },
    },
)
async def proxy_api(
    path: str,
    request: Request,
    user_id: int = Depends(verify_token_and_get_user_id),
    orchestrator_client=Depends(get_orchestrator_client),
):
    """
    Proxy authenticated API requests to Orchestrator service.

    Args:
        path: API path to proxy (e.g., 'images', 'containers', 'images/1')
        request: FastAPI request object
        user_id: Authenticated user ID (from token)
        orchestrator_client: Orchestrator client (injected)

    Returns:
        Response: Proxied response from Orchestrator service
    """
    return await handle_orchestrator_proxy(
        request=request,
        path=path,
        user_id=user_id,
        orchestrator_client=orchestrator_client,
    )
