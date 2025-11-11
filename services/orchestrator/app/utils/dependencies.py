from fastapi import Header, HTTPException

def get_user_id(x_user_id: str = Header(..., alias="X-User-Id")) -> int:
    try:
        return int (x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id in header"
        )