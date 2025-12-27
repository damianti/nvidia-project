from typing import Optional

from fastapi import Header, HTTPException, Request


def build_bearer_auth_header(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    *,
    allow_authorization_header: bool = True,
) -> Optional[str]:
    """
    Build a Bearer authorization header from the incoming request.

    Priority:
    1) Cookie-based auth (HttpOnly cookie): access_token
    2) Authorization header (for API clients / CLI) if enabled

    Args:
        request: FastAPI request
        authorization: Optional Authorization header (FastAPI will inject it)
        allow_authorization_header: If False, ignores Authorization header completely

    Returns:
        A string like "Bearer <token>" or None if not found
    """
    # 1) Cookie first (preferred for browser UI)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return f"Bearer {cookie_token}"

    # 2) Optional Authorization header (preferred for API clients)
    if not allow_authorization_header:
        return None

    if authorization and isinstance(authorization, str):
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Invalid authorization header format"
            )
        return authorization

    return None
