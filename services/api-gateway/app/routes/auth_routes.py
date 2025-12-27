from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.schemas.user import (
    LoginRequest,
    UserCreate,
    LoginResponse,
    UserResponse,
    LogoutResponse,
    ErrorResponse,
)
from app.clients.auth_client import AuthClient
from app.utils.dependencies import get_auth_client
from app.services import auth_service
from app.utils.auth import build_bearer_auth_header


router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=200,
    summary="Authenticate user",
    description="Authenticate user credentials and receive JWT token. The token is automatically set as an HttpOnly cookie for security.",
    response_description="User information and authentication token",
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
async def login_user(
    login_data: LoginRequest,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client),
):
    """
    Authenticate user and get JWT token.

    The JWT token is automatically set as an HttpOnly cookie for security.
    The token can also be used in the Authorization header for API clients.

    Args:
        login_data: User credentials (email and password)
        response: FastAPI response object (used to set cookie)
        auth_client: Auth service client (injected)

    Returns:
        LoginResponse: User information and token details
    """
    return await auth_service.handle_login(login_data, auth_client, response)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=200,
    summary="Logout user",
    description="Invalidate user session and remove JWT token cookie. Requires authentication.",
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
async def logout_user(
    request: Request,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client),
):
    """
    Logout user and invalidate session.

    Removes the JWT token cookie and invalidates the session on the auth-service.
    Requires a valid authentication token.

    Args:
        request: FastAPI request object (used to extract auth token)
        response: FastAPI response object (used to remove cookie)
        auth_client: Auth service client (injected)

    Returns:
        LogoutResponse: Logout confirmation message
    """
    authorization_header = build_bearer_auth_header(
        request, allow_authorization_header=True
    )
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await auth_service.handle_logout(
        authorization_header, auth_client, response, request
    )


@router.post(
    "/signup",
    response_model=LoginResponse,
    status_code=201,
    summary="Register new user",
    description="Create a new user account. The user will be automatically logged in and receive a JWT token.",
    response_description="User information and authentication token",
    responses={
        200: {
            "description": "User created successfully",
            "model": LoginResponse,
        },
        400: {
            "description": "User already exists or validation error",
            "model": ErrorResponse,
        },
        422: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
    },
)
async def signup_user(
    user_data: UserCreate,
    response: Response,
    auth_client: AuthClient = Depends(get_auth_client),
):
    """
    Register a new user account.

    Creates a new user account and automatically logs them in.
    The JWT token is set as an HttpOnly cookie.

    Args:
        user_data: User registration data (username, email, password)
        response: FastAPI response object (used to set cookie)
        auth_client: Auth service client (injected)

    Returns:
        LoginResponse: User information and token details
    """
    return await auth_service.handle_signup(user_data, auth_client, response)


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
async def get_current_user(
    request: Request, auth_client: AuthClient = Depends(get_auth_client)
):
    """
    Get current authenticated user information.

    Retrieves the user information for the currently authenticated user
    based on the JWT token in the cookie or Authorization header.

    Args:
        request: FastAPI request object (used to extract auth token)
        auth_client: Auth service client (injected)

    Returns:
        UserResponse: Current user information
    """
    authorization_header = build_bearer_auth_header(
        request, allow_authorization_header=False
    )
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await auth_service.handle_get_current_user(
        authorization_header, auth_client, request
    )
