from fastapi import APIRouter, Depends, Response
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
from app.services import auth_service
from app.utils import security

router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=200,
    summary="Authenticate user",
    description="Authenticate user credentials and receive JWT token. The token is automatically set as an HttpOnly cookie for security.",
    response_description="User information (token set as cookie)",
    responses={
        200: {
            "description": "Login successful",
            "model": LoginResponse,
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
    },
)
async def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and get JWT token.

    The JWT token is automatically set as an HttpOnly cookie for security.
    The token can also be used in the Authorization header for API clients.

    Args:
        credentials: User credentials (email and password)
        response: FastAPI response object (used to set cookie)
        db: Database session (injected)

    Returns:
        LoginResponse: User information (token is set as cookie)
    """
    user, token = auth_service.login(credentials, db)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # True in prod
        samesite="lax",  # Changed from "strict" to "lax" for better compatibility
        max_age=3600,
        path="/",
    )
    return {"user": user}


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
    summary="Register new user",
    description="Create a new user account with email and password. The user will be automatically logged in and receive a JWT token.",
    response_description="User information",
    responses={
        201: {
            "description": "User created successfully",
            "model": UserResponse,
        },
        400: {
            "description": "User already exists",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
    },
)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Creates a new user account with the provided email, username, and password.

    Args:
        user_data: User registration data (username, email, password)
        db: Database session (injected)

    Returns:
        UserResponse: Created user information
    """
    return auth_service.signup(user_data, db)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=200,
    summary="Logout user",
    description="Logout user by removing JWT token cookie. Requires authentication.",
    response_description="Logout confirmation",
    responses={
        200: {
            "description": "Logout successful",
            "model": LogoutResponse,
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
        },
    },
)
async def logout(response: Response):
    """
    Logout user and invalidate session.

    Removes the JWT token cookie from the client.

    Args:
        response: FastAPI response object (used to remove cookie)

    Returns:
        LogoutResponse: Logout confirmation message
    """
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
        200: {
            "description": "User information retrieved successfully",
            "model": UserResponse,
        },
        401: {
            "description": "Authentication required or invalid token",
            "model": ErrorResponse,
        },
    },
)
async def get_current_user_info(
    current_user: User = Depends(security.get_current_user),
):
    """
    Get current authenticated user information.

    Retrieves the user information for the currently authenticated user
    based on the JWT token in the cookie or Authorization header.

    Args:
        current_user: Authenticated user (from token, injected)

    Returns:
        UserResponse: Current user information
    """
    return current_user
