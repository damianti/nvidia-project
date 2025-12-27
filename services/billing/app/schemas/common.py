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
                    "detail": "No billing records found for image 1 or image does not belong to user"
                },
                {
                    "detail": "Failed to retrieve billing summaries"
                },
                {
                    "detail": "Authentication required"
                }
            ]
        }
    )

