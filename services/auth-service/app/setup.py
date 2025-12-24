"""
Database setup and initialization utilities.

This module handles initial database setup tasks like creating default users.
This is initialization code, not business logic.
"""

from app.database.config import SessionLocal
from app.services import user_service
from app.utils import passwords
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


def create_default_user_if_needed() -> bool:
    """
    Create default user if no users exist in the database.

    This is called during service startup to ensure there's at least one user
    for initial access. This is initialization code, not business logic.

    Returns:
        bool: True if user was created, False if users already exist
    """
    db = SessionLocal()
    try:
        user_count = user_service.count_users(db)

        if user_count == 0:
            logger.info(
                "setup.creating_default_user",
                extra={
                    "service_name": SERVICE_NAME,
                    "username": "example",
                    "email": "example@gmail.com",
                },
            )

            # Hash password and create user (initialization code)
            hashed_password = passwords.get_password_hash("example123")
            user_service.create_user(
                email="example@gmail.com",
                username="example",
                hashed_password=hashed_password,
                db=db,
            )

            logger.info(
                "setup.default_user_created",
                extra={
                    "service_name": SERVICE_NAME,
                    "username": "example",
                    "email": "example@gmail.com",
                },
            )
            return True
        else:
            logger.info(
                "setup.users_exist",
                extra={"service_name": SERVICE_NAME, "user_count": user_count},
            )
            return False
    except Exception as e:
        logger.error(
            "setup.default_user_error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "service_name": SERVICE_NAME,
            },
            exc_info=True,
        )
        # Don't raise - allow service to start even if default user creation fails
        return False
    finally:
        db.close()
