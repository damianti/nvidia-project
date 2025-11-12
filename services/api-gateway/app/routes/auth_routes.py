from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.schemas.user import LoginRequest, UserCreate
from app.clients.auth_client import AuthClient
from app.utils.dependencies import get_auth_client
from app.services import auth_service 


router = APIRouter(tags=["auth"])

def get_authorization_header(
    authorization: Optional[str] = Header(default=None, alias="Authorization")
) -> str:
    """Extract and validate Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    return authorization

@router.post("/login")
async def login_user(
    login_data: LoginRequest,
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_login(login_data, auth_client)

@router.post("/logout")
async def logout_user(
    authorization_header: str = Depends(get_authorization_header),
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_logout(authorization_header, auth_client)

@router.post("/signup")
async def signup_user(
    user_data: UserCreate,
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_signup(user_data, auth_client)

@router.get("/me")
async def get_current_user(
    authorization_header: str = Depends(get_authorization_header),
    auth_client: AuthClient = Depends(get_auth_client)
):  
    return await auth_service.handle_get_current_user(authorization_header, auth_client)

