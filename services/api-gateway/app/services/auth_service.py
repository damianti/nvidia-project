from fastapi import HTTPException, Response, Request

from app.clients.auth_client import AuthClient
from app.schemas.user import LoginRequest, UserCreate

async def handle_login(login_data: LoginRequest, auth_client: AuthClient, response: Response):
    auth_response = await auth_client.login(login_data.dict())
    
    # Copy Set-Cookie header from auth-service response (httpx uses lowercase headers)
    set_cookie = auth_response.headers.get("set-cookie") or auth_response.headers.get("Set-Cookie")
    if set_cookie:
        response.headers["Set-Cookie"] = set_cookie
    
    if auth_response.status_code == 200:
        return auth_response.json()
    
    error_data = auth_response.json()
    raise HTTPException(
        status_code=auth_response.status_code,
        detail=error_data.get("detail", "Login failed")
    )

async def handle_signup(user_data: UserCreate, auth_client: AuthClient, response: Response):
    auth_response = await auth_client.signup(user_data.dict())
    
    # Copy Set-Cookie header from auth-service response (httpx uses lowercase headers)
    set_cookie = auth_response.headers.get("set-cookie") or auth_response.headers.get("Set-Cookie")
    if set_cookie:
        response.headers["Set-Cookie"] = set_cookie
    
    if auth_response.status_code == 200:
        return auth_response.json()
    
    error_data = auth_response.json()
    raise HTTPException(
        status_code=auth_response.status_code,
        detail=error_data.get("detail", "Signup failed")
    )

async def handle_get_current_user(authorization_header: str, auth_client: AuthClient, request: Request):
    # Get cookies from request to forward to auth-service
    cookies = request.cookies
    auth_response = await auth_client.get_current_user(authorization_header, cookies)
    
    if auth_response.status_code == 200:
        return auth_response.json()
    
    error_data = auth_response.json()
    raise HTTPException(
        status_code=auth_response.status_code,
        detail=error_data.get("detail", "Failed to get current user")
    )

async def handle_logout(authorization_header: str, auth_client: AuthClient, response: Response, request: Request = None):
    # Extract token from authorization header for logout
    token = authorization_header.replace("Bearer ", "")
    # Get cookies from request to forward to auth-service
    cookies = request.cookies if request else None
    auth_response = await auth_client.logout(token, cookies)
    
    # Copy Set-Cookie header from auth-service response (httpx uses lowercase headers)
    set_cookie = auth_response.headers.get("set-cookie") or auth_response.headers.get("Set-Cookie")
    if set_cookie:
        response.headers["Set-Cookie"] = set_cookie
    
    if auth_response.status_code == 200:
        return auth_response.json()
    
    error_data = auth_response.json()
    raise HTTPException(
        status_code=auth_response.status_code,
        detail=error_data.get("detail", "Failed to logout")
    )
    