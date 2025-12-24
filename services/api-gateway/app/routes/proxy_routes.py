from fastapi import APIRouter, Request, Response, Depends, UploadFile, File, Form

from app.utils.dependencies import (
    get_cached_memory,
    get_lb_client,
    get_orchestrator_client,
    get_http_client,
)
from app.services.routing_cache import Cache
from app.services.gateway_service import handle_route_request, RouteValidationError
from app.services.orchestrator_service import (
    handle_orchestrator_proxy,
    handle_image_upload,
)
from app.utils.dependencies import verify_token_and_get_user_id

router = APIRouter(tags=["proxy"])


@router.api_route(
    "/route",
    methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    summary="Route request to container via Load Balancer",
)
async def post_route(
    request: Request,
    cached_memory: Cache = Depends(get_cached_memory),
    lb_client=Depends(get_lb_client),
    http_client=Depends(get_http_client),
):
    """Route HTTP request to appropriate container based on Host header using Load Balancer"""
    try:
        # Modo legacy: usamos el Host normalizado como app_hostname
        # y no hay remaining_path específico (usamos "/").
        host = request.headers.get("Host", "").split("/")[0]
        app_hostname = host.split(":")[0] if host else ""
        if not app_hostname:
            return Response(content="Missing Host header", status_code=400)
        return await handle_route_request(
            request=request,
            app_hostname=app_hostname,
            remaining_path="/",
            http_client=http_client,
            cached_memory=cached_memory,
            lb_client=lb_client,
        )
    except RouteValidationError as e:
        return Response(content=e.message, status_code=e.status_code)


@router.api_route(
    "/apps/{app_hostname}/{remaining_path:path}",
    methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    summary="Proxy HTTP requests to user apps via Load Balancer",
)
async def apps_route(
    request: Request,
    app_hostname: str,
    remaining_path: str,
    cached_memory: Cache = Depends(get_cached_memory),
    lb_client=Depends(get_lb_client),
    http_client=Depends(get_http_client),
):
    try:
        # Validamos app_hostname por si viene vacío o solo espacios
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
        )
    except RouteValidationError as e:
        return Response(content=e.message, status_code=e.status_code)


@router.post("/api/images", summary="Upload image with multipart/form-data")
async def upload_image(
    name: str = Form(...),
    tag: str = Form(...),
    app_hostname: str = Form(...),
    container_port: int = Form(8080),
    min_instances: int = Form(1),
    max_instances: int = Form(3),
    cpu_limit: str = Form("0.5"),
    memory_limit: str = Form("512m"),
    file: UploadFile = File(...),
    user_id: int = Depends(verify_token_and_get_user_id),
    orchestrator_client=Depends(get_orchestrator_client),
):
    """Upload image with Dockerfile (multipart/form-data)"""
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
    )


@router.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
    summary="Proxy API requests to Orchestrator service",
)
async def proxy_api(
    path: str,
    request: Request,
    user_id: int = Depends(verify_token_and_get_user_id),
    orchestrator_client=Depends(get_orchestrator_client),
):
    """Proxy authenticated API requests to Orchestrator service for container and image management"""
    return await handle_orchestrator_proxy(
        request=request,
        path=path,
        user_id=user_id,
        orchestrator_client=orchestrator_client,
    )
