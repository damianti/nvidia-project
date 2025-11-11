# Orchestrator Service - High-level orchestration for orchestrator proxy operations
from fastapi import Request, Response

from app.clients.orchestrator_client import OrchestratorClient


async def handle_orchestrator_proxy(
    request: Request,
    path: str,
    user_id: int,
    orchestrator_client: OrchestratorClient
) -> Response:
    """
    Handle proxy request to Orchestrator API.
    
    Args:
        request: FastAPI request object
        path: API path to proxy
        orchestrator_client: Orchestrator client instance
        
    Returns:
        FastAPI Response with proxied content
    """
    body = await request.body()
    query_params = dict(request.query_params) if request.query_params else None
    headers = {"X-User-Id": str(user_id)}

    response = await orchestrator_client.proxy_request(
        method=request.method,
        path=f"/api/{path}",
        query_params=query_params,
        body=body if body else None,
        headers=headers
    )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

