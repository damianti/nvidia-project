from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Image not found"},
                {"detail": "Container not found"},
                {"detail": "Authentication required"},
                {"detail": "Validation error"},
            ]
        }
    )


class MessageResponse(BaseModel):
    message: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Image 1 deleted successfully"}}
    )


class BuildLogsResponse(BaseModel):
    build_logs: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"build_logs": "Step 1/5 : FROM python:3.11\n..."}
        }
    )


class PaginationParams(BaseModel):
    """Query params for paginated list endpoints."""

    page: int = 1
    page_size: int = 50

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
