# Orchestrator Service - High-level orchestration for orchestrator proxy operations
from fastapi import Request, Response, UploadFile
from typing import Optional
import httpx

from app.clients.orchestrator_client import OrchestratorClient


async def handle_image_upload(
    name: str,
    tag: str,
    app_hostname: str,
    container_port: int,
    min_instances: int,
    max_instances: int,
    cpu_limit: str,
    memory_limit: str,
    file: UploadFile,
    user_id: int,
    orchestrator_client: OrchestratorClient
) -> Response:
    """Handle image upload with multipart/form-data"""
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {
        "file": (file.filename, file_content, file.content_type or "application/octet-stream")
    }
    data = {
        "name": name,
        "tag": tag,
        "app_hostname": app_hostname,
        "container_port": str(container_port),
        "min_instances": str(min_instances),
        "max_instances": str(max_instances),
        "cpu_limit": cpu_limit,
        "memory_limit": memory_limit,
    }
    
    # Send to Orchestrator
    url = f"{orchestrator_client.base_url}/api/images"
    headers = {"X-User-Id": str(user_id)}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url,
            headers=headers,
            files=files,
            data=data,
            timeout=orchestrator_client.timeout_s
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )


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
    query_params = dict(request.query_params) if request.query_params else None
    headers = {"X-User-Id": str(user_id)}
    
    # Check if this is a multipart/form-data request
    content_type = str(request.headers.get("Content-Type", ""))
    is_multipart = "multipart/form-data" in content_type
    
    if is_multipart:
        # For multipart requests, try to read raw body
        # Note: Once FastAPI starts parsing, the stream may be consumed
        # So we try to read it before it's parsed
        try:
            body_chunks = []
            async for chunk in request.stream():
                body_chunks.append(chunk)
            body = b"".join(body_chunks)
            
            # If body is empty, FastAPI may have already consumed it
            # In that case, we need to reconstruct from form data
            if not body or len(body) == 0:
                # Fallback: try to get form data (may not work for generic endpoints)
                try:
                    form_data = await request.form()
                    # Reconstruct multipart manually would be complex
                    # For now, log error and return 500
                    import logging
                    logger = logging.getLogger("api-gateway")
                    logger.error("Multipart body was consumed by FastAPI, cannot reconstruct")
                    return Response(
                        content='{"detail": "Multipart form data cannot be proxied through generic endpoint"}',
                        status_code=500,
                        media_type="application/json"
                    )
                except Exception:
                    pass
        except Exception as e:
            import logging
            logger = logging.getLogger("api-gateway")
            logger.error(f"Error reading multipart stream: {e}")
            return Response(
                content=f'{{"detail": "Error processing multipart request: {str(e)}"}}',
                status_code=500,
                media_type="application/json"
            )
        
        # Preserve the Content-Type header with boundary
        headers["Content-Type"] = content_type
        
        response = await orchestrator_client.proxy_request(
            method=request.method,
            path=f"/api/{path}",
            query_params=query_params,
            body=body,
            headers=headers
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    else:
        # For non-multipart requests, use the original body-based approach
        body = await request.body()
        if content_type:
            headers["Content-Type"] = content_type
        
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

