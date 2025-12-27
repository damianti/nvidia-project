from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "username": "johndoe",
                    "email": "john@example.com",
                    "password": "securepassword123",
                },
                {
                    "username": "janedoe",
                    "email": "jane@example.com",
                    "password": "mypassword456",
                },
            ]
        }
    )


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "created_at": "2024-01-01T00:00:00Z",
            }
        },
    )


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"email": "user@example.com", "password": "securepassword123"},
                {"email": "admin@example.com", "password": "admin123"},
            ]
        }
    )


class LoginResponse(BaseModel):
    user: UserResponse

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "created_at": "2024-01-01T00:00:00Z",
                }
            }
        }
    )


class LogoutResponse(BaseModel):
    message: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Successfully logged out"}}
    )


class ErrorResponse(BaseModel):
    detail: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Invalid email or password"},
                {"detail": "User already exists"},
                {"detail": "Authentication required"},
                {"detail": "Validation error"},
            ]
        }
    )


class TokenData(BaseModel):
    username: Optional[str] = None
