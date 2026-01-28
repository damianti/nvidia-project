from typing import Optional, Tuple
from fastapi import Request, Response, UploadFile
import httpx

from app.clients.orchestrator_client import OrchestratorClient
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME
from app.services.user_id_cache import UserIdCache

logger = setup_logger(SERVICE_NAME)


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
    orchestrator_client: OrchestratorClient,
    user_id_cache: UserIdCache,
) -> Response:
    """Upload image to Orchestrator service with multipart/form-data."""
    file_content = await file.read()

    files = {
        "file": (
            file.filename,
            file_content,
            file.content_type or "application/octet-stream",
        )
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

    url = f"{orchestrator_client.base_url}/api/images/"
    headers = {"X-User-Id": str(user_id)}

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            url=url,
            headers=headers,
            files=files,
            data=data,
            timeout=orchestrator_client.timeout_s,
        )
        # If image creation was successful, update user_id cache
        if response.status_code == 201:
            user_id_cache.set(app_hostname, user_id)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


async def _read_multipart_body(
    request: Request,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Read multipart body from request stream.

    Returns:
        Tuple of (body bytes, error message). Returns (None, error_msg) on failure.
    """
    try:
        body_chunks = []
        async for chunk in request.stream():
            body_chunks.append(chunk)
        body = b"".join(body_chunks)

        if not body:
            try:
                await request.form()
                logger.error(
                    "orchestrator.multipart.body_consumed",
                    extra={"path": request.url.path},
                )
                return (
                    None,
                    "Multipart form data cannot be proxied through generic endpoint",
                )
            except Exception:
                pass

        return body, None
    except Exception as e:
        logger.error(
            "orchestrator.multipart.read_error",
            extra={"path": request.url.path, "error": str(e)},
            exc_info=True,
        )
        return None, f"Error processing multipart request: {str(e)}"


async def handle_orchestrator_proxy(
    request: Request,
    path: str,
    user_id: int,
    orchestrator_client: OrchestratorClient,
) -> Response:
    """Proxy request to Orchestrator API."""
    query_params = dict(request.query_params) if request.query_params else None
    headers = {"X-User-Id": str(user_id)}
    content_type = str(request.headers.get("Content-Type", ""))
    is_multipart = "multipart/form-data" in content_type

    if is_multipart:
        body, error_msg = await _read_multipart_body(request)
        if body is None:
            return Response(
                content=f'{{"detail": "{error_msg}"}}',
                status_code=500,
                media_type="application/json",
            )
        headers["Content-Type"] = content_type
    else:
        body = await request.body()
        if content_type:
            headers["Content-Type"] = content_type

    response = await orchestrator_client.proxy_request(
        method=request.method,
        path=f"/api/{path}",
        query_params=query_params,
        body=body if body else None,
        headers=headers,
    )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
