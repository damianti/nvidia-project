from fastapi import Request
from app.utils.logger import correlation_id_var


def extract_client_ip(request: Request) -> str:
    """Extracts client IP from request, handling X-Forwarded-For header"""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
        return client_ip
    
    return request.client.host if request.client.host is not None else ""


def normalize_website_url(url: str) -> str:
    """Normalizes website_url: lowercase, strip, removes protocol and port"""
    if not url:
        return ""
    normalized = url.strip().lower()
    # Remove protocol if exists
    if normalized.startswith("https://"):
        normalized = normalized[8:]  # len("https://") = 8
    elif normalized.startswith("http://"):
        normalized = normalized[7:]  # len("http://") = 7
    # Remove port if exists (e.g., localhost:8080 -> localhost)
    if ":" in normalized:
        normalized = normalized.split(":")[0]
    # Remove trailing slash optional
    normalized = normalized.rstrip("/")
    return normalized


def prepare_proxy_headers(request: Request) -> dict:
    """Prepares headers for proxy, removing host and content-length, adding correlation ID"""
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    corr_id = correlation_id_var.get()
    if corr_id and "X-Correlation-ID" not in headers:
        headers["X-Correlation-ID"] = corr_id
    return headers
