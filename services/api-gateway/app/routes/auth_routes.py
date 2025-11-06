from fastapi import APIRouter, Depends

from app.schemas.user import LoginRequest, UserCreate
from app.clients.auth_client import AuthClient
from app.utils.dependencies import get_auth_client

from app.services import auth_service 

router = APIRouter(tags=["auth"])

@router.post("/login")
async def login_user(
    login_data: LoginRequest,
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_login(login_data, auth_client)

@router.post("/signup")
async def signup_user(
    user_data: UserCreate,
    auth_client: AuthClient = Depends(get_auth_client)
):
    return await auth_service.handle_signup(user_data, auth_client)

@router.get("/me")
async def get_current_user(

)
