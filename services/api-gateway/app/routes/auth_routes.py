from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response
from typing import Optional

from app.schemas.user import LoginRequest, UserCreate
from app.clients.auth_client import AuthClient
from app.utils.dependencies import get_auth_client
from app.services import auth_service 


router = APIRouter(tags=["auth"])

def get_authorization_header(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization")
) -> Optional[str]:
    """Extract Authorization header or token from cookies"""
    # Try to get token from cookies first
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return f"Bearer {cookie_token}"
    elif authorization and isinstance(authorization, str):
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        return authorization
    return None

@router.post("/login", summary="Authenticate user and get JWT token")
async def login_user(
    login_data: LoginRequest,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client)
):
    """Proxy login request to auth-service and return JWT token in HttpOnly cookie"""
    return await auth_service.handle_login(login_data, auth_client, response)

@router.post("/logout", summary="Logout user and invalidate session")
async def logout_user(
    request: Request,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client)
):
    """Proxy logout request to auth-service and remove JWT token cookie"""
    authorization_header = get_authorization_header(request)
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await auth_service.handle_logout(authorization_header, auth_client, response, request)

@router.post("/signup", summary="Register a new user")
async def signup_user(
    user_data: UserCreate,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client)
):
    """Proxy signup request to auth-service to create a new user account"""
    return await auth_service.handle_signup(user_data, auth_client, response)

@router.get("/me", summary="Get current authenticated user information")
async def get_current_user(
    request: Request,
    auth_client: AuthClient = Depends(get_auth_client)
):  
    """Proxy request to auth-service to retrieve current authenticated user information"""
    authorization_header = get_authorization_header(request)
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await auth_service.handle_get_current_user(authorization_header, auth_client, request)

