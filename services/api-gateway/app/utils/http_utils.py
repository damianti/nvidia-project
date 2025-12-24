from fastapi import Request
from app.utils.logger import correlation_id_var


def extract_client_ip(request: Request) -> str:
    """Extracts client IP from request, handling X-Forwarded-For header"""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
        return client_ip

    return request.client.host if request.client.host is not None else ""


def prepare_proxy_headers(request: Request) -> dict:
    """Prepares headers for proxy, removing host and content-length, adding correlation ID"""
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    corr_id = correlation_id_var.get()
    if corr_id and "X-Correlation-ID" not in headers:
        headers["X-Correlation-ID"] = corr_id
    return headers
