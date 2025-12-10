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
    elif authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        return authorization
    return None

@router.post("/login")
async def login_user(
    login_data: LoginRequest,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_login(login_data, auth_client, response)

@router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client)
):
    authorization_header = get_authorization_header(request)
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await auth_service.handle_logout(authorization_header, auth_client, response, request)

@router.post("/signup")
async def signup_user(
    user_data: UserCreate,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_signup(user_data, auth_client, response)

@router.get("/me")
async def get_current_user(
    request: Request,
    auth_client: AuthClient = Depends(get_auth_client)
):  
    authorization_header = get_authorization_header(request)
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await auth_service.handle_get_current_user(authorization_header, auth_client, request)

