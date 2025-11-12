from fastapi import HTTPException

from app.clients.auth_client import AuthClient
from app.schemas.user import LoginRequest, UserCreate

async def handle_login(login_data: LoginRequest, auth_client: AuthClient):
    response = await auth_client.login(login_data.dict())
    
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=error_data.get("detail", "Login failed")
    )
async def handle_signup(user_data: UserCreate, auth_client: AuthClient):
    response = await auth_client.signup(user_data.dict())
    
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=error_data.get("detail", "Signup failed")
    )

async def handle_get_current_user(authorization_header: str, auth_client: AuthClient):
    response = await auth_client.get_current_user(authorization_header)
    
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=error_data.get("detail", "Failed to get current user")
    )
async def handle_logout(authorization_header: str, auth_client: AuthClient):
    response = await auth_client.logout(authorization_header)
    
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=error_data.get("detail", "Failed to logout")
    )
    