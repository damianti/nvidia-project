from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session



from app.database.config import get_db
from app.database.models import User 
from app.schemas.user import UserCreate, UserResponse, LoginRequest
from app.services import auth_service
from app.utils import security


router = APIRouter(tags=["authentication"])


# Auth endpoints
@router.post("/login")
async def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    ):
    """Authenticate user and return JWT token"""
    user, token = auth_service.login(credentials, db)
    response.set_cookie(
         key="access_token",
         value=token,
         httponly=True,
         secure=False,  # True in prod
         samesite="strict",
         max_age=3600,
         path="/",
     )
    return {"user": user}
        
    

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return auth_service.signup(user_data, db)
    

@router.post("/logout")
async def logout(response: Response):
    """Logout user and discard token"""
    response.delete_cookie("access_token", path="/")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(security.get_current_user)):
    """Get current user information"""
    return current_user
