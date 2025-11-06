from pydantic import EmailStr
from sqlalchemy.orm import Session

from typing import Optional
from app.database.models import User


def get_user_by_email(email: EmailStr, db: Session)-> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(username: str, db: Session)-> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def create_user(email: EmailStr, username: str,  hashed_password: str, db: Session)-> User:

    db_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        
    db.add(db_user)
    db.flush()

    return db_user