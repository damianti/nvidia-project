from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    detail: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "Image not found"
                },
                {
                    "detail": "Container not found"
                },
                {
                    "detail": "Authentication required"
                },
                {
                    "detail": "Validation error"
                }
            ]
        }
    )


class MessageResponse(BaseModel):
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Image 1 deleted successfully"
            }
        }
    )


class BuildLogsResponse(BaseModel):
    build_logs: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "build_logs": "Step 1/5 : FROM python:3.11\n..."
            }
        }
    )

