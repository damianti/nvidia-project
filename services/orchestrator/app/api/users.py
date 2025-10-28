from fastapi import APIRouter
from app.schemas.user import UserCreate, UserResponse
from app.database.config import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.database.models import User
from typing import List

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password  # In production, hash the password!
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).all()
    return users
