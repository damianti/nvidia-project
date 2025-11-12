from fastapi import APIRouter, Request, Response, Depends

from app.utils.dependencies import (
    get_cached_memory, 
    get_lb_client, 
    get_orchestrator_client, 
    get_http_client
)
from app.services.routing_cache import Cache
from app.services.gateway_service import handle_route_request, RouteValidationError
from app.services.orchestrator_service import handle_orchestrator_proxy
from app.utils.dependencies import verify_token_and_get_user_id
router = APIRouter(tags=["proxy"])

@router.api_route("/route", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
async def post_route(
    request: Request,
    cached_memory: Cache = Depends(get_cached_memory),
    lb_client = Depends(get_lb_client),
    http_client = Depends(get_http_client)
):
    """Route request to container based on Host header"""
    try:
        return await handle_route_request(
            request=request,
            http_client=http_client,
            cached_memory=cached_memory,
            lb_client=lb_client
        )
    except RouteValidationError as e:
        return Response(content=e.message, status_code=e.status_code)


@router.api_route("/api/{path:path}", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
async def proxy_api(
    path: str,
    request: Request,
    user_id: int = Depends(verify_token_and_get_user_id),
    orchestrator_client = Depends(get_orchestrator_client)
):
    """Proxy API requests to Orchestrator"""
    return await handle_orchestrator_proxy(
        request=request,
        path=path,
        user_id=user_id,
        orchestrator_client=orchestrator_client
    )
