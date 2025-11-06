from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session



from app.database.config import get_db
from app.database.models import User 
from app.schemas.user import UserCreate, UserResponse, LoginResponse, LoginRequest
from app.services import auth_service
from app.utils import security


router = APIRouter(tags=["authentication"])


# Auth endpoints
@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    return auth_service.login(login_data, db)
        
    

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return auth_service.signup(user_data, db)
    

@router.post("/logout")
async def logout():
    """Logout user (client should discard token)"""
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(security.get_current_user)):
    """Get current user information"""
    return current_user
