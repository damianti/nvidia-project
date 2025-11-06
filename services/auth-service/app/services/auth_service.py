from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.database.models import User 
from app.schemas.user import UserCreate, LoginResponse, LoginRequest
from app.services import user_service
from app.utils import passwords, tokens
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME
from app.exceptions.domain import UserNotFoundError, UserAlreadyExistsError, DatabaseError, InvalidPasswordError

logger = setup_logger(SERVICE_NAME)

def authenticate_user(email: EmailStr, password: str, db: Session) -> User:
    """Authenticates a user and returns the user if successful"""
    user = user_service.get_user_by_email(email, db)
    
    if not passwords.verify_password(password, user.password):
        raise InvalidPasswordError("Incorrect password")
    
    return user


def login(login_data: LoginRequest, db: Session) -> LoginResponse:
    logger.info(
        "auth.login.attempt",
        extra={"email": login_data.email, "service_name": SERVICE_NAME}
    )
    
    try:
        user = authenticate_user(login_data.email, login_data.password, db)
        access_token = tokens.create_access_token(data={"sub": user.username})    
    
        logger.info(
        "auth.login.success",
        extra={"user_id": user.id, "username": user.username, "service_name": SERVICE_NAME}
        )
        
        return LoginResponse(
            access_token= access_token,
            token_type= "bearer",
            user= user
        )

    except (UserNotFoundError, InvalidPasswordError) as e:
        logger.warning(
            "auth.login.failed",
            extra={
                "email": login_data.email,
                "error_type": type(e).__name__,
                "service_name": SERVICE_NAME
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        ) from e
    
    except Exception as e:
        logger.error(
            "auth.login.error",
            extra={
                "email": login_data.email,
                "error": str(e),
                "service_name": SERVICE_NAME
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        ) from e
        

def signup(user_data: UserCreate, db: Session) -> User:
    logger.info(
        "auth.signup.attempt",
        extra={"email": user_data.email, "username": user_data.username, "service_name": SERVICE_NAME}
    )
    
    hashed_password = passwords.get_password_hash(user_data.password)
    
    try:
        db_user = user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            db=db
        )
        
        logger.info(
            "auth.signup.success",
            extra={"user_id": db_user.id, "email": db_user.email, "username": db_user.username, "service_name": SERVICE_NAME}
        )
        
        return db_user

    except UserAlreadyExistsError as e:
        logger.warning(
            "auth.signup.user_already_exists",
            extra={"email": user_data.email, "username": user_data.username, "service_name": SERVICE_NAME}
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
    except DatabaseError as e:
        logger.error(
            "auth.signup.database_error",
            extra={
                "email": user_data.email,
                "username": user_data.username,
                "error": str(e),
                "service_name": SERVICE_NAME
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while creating user"
        ) from e