from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.database.models import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    ErrorResponse,
)
from app.services import auth_service, token_blocklist
from app.utils import security
from app.utils.config import SECURE_COOKIES, ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils import tokens as token_utils

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=200,
    summary="Authenticate user",
    description="Authenticate user credentials and receive JWT token. The token is automatically set as an HttpOnly cookie for security.",
    response_description="User information (token set as cookie)",
    responses={
        200: {"description": "Login successful", "model": LoginResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        429: {"description": "Too many requests", "model": ErrorResponse},
    },
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user, token = auth_service.login(credentials, db)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return {"user": user}


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
    summary="Register new user",
    description="Create a new user account with email and password.",
    response_description="User information",
    responses={
        201: {"description": "User created successfully", "model": UserResponse},
        400: {"description": "User already exists", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        429: {"description": "Too many requests", "model": ErrorResponse},
    },
)
@limiter.limit("3/minute")
async def signup(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    return auth_service.signup(user_data, db)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=200,
    summary="Logout user",
    description="Logout user by removing JWT token cookie and revoking the token. Requires authentication.",
    response_description="Logout confirmation",
    responses={
        200: {"description": "Logout successful", "model": LogoutResponse},
        401: {"description": "Authentication required", "model": ErrorResponse},
    },
)
async def logout(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = token_utils.decode_access_token(token)
            exp_claim = token_utils._get_exp_from_token(token)
            if exp_claim:
                remaining = int(exp_claim - datetime.now(timezone.utc).timestamp())
                if remaining > 0:
                    token_blocklist.block_token(token, ttl_seconds=remaining)
        except Exception:
            pass

    response.delete_cookie("access_token", path="/")
    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=200,
    summary="Get current user",
    description="Retrieve information about the currently authenticated user. Requires authentication.",
    response_description="Current user information",
    responses={
        200: {"description": "User information retrieved successfully", "model": UserResponse},
        401: {"description": "Authentication required or invalid token", "model": ErrorResponse},
    },
)
async def get_current_user_info(
    current_user: User = Depends(security.get_current_user),
):
    return current_user
