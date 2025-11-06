from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.utils import tokens
from app.schemas.user import TokenData
from app.services import user_service
from app.database.models import User
from app.database.config import get_db
from app.exceptions.domain import TokenExpiredError, InvalidTokenError, UserNotFoundError

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    try:
        return tokens.decode_access_token(credentials.credentials)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    token_data: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    try:
        return user_service.get_user_by_username(token_data.username, db)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
