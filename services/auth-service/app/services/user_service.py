from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database.models import User
from app.repositories import user_repository
from app.exceptions.domain import (
    UserAlreadyExistsError,
    DatabaseError,
    UserNotFoundError,
)


def get_user_by_email(email: EmailStr, db: Session) -> User:
    user = user_repository.get_user_by_email(email, db)
    if not user:
        raise UserNotFoundError(f"User with email {email} not found")
    return user


def get_user_by_username(username: str, db: Session) -> User:
    user = user_repository.get_user_by_username(username, db)
    if not user:
        raise UserNotFoundError(f"User with username {username} not found")
    return user


def create_user(
    email: EmailStr, username: str, hashed_password: str, db: Session
) -> User:
    """Creates a new user with already hashed password"""
    try:
        user = user_repository.create_user(email, username, hashed_password, db)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError as e:
        db.rollback()
        raise UserAlreadyExistsError(
            f"User with email {email} or username {username} already exists"
        ) from e

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(
            f"Database error occurred while creating user: {str(e)}"
        ) from e


def count_users(db: Session) -> int:
    """Count total number of users in the database"""
    return user_repository.count_users(db)
