from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Tuple

from app.database.models import Image


def create(db: Session, image: Image) -> Image:
    """Persist a new Image. Does not commit; caller controls the transaction."""
    db.add(image)
    return image


def get_by_id(db: Session, image_id: int, user_id: int) -> Optional[Image]:
    return (
        db.query(Image)
        .filter(Image.user_id == user_id)
        .filter(Image.id == image_id)
        .first()
    )


def get_all_images(
    db: Session, user_id: int, offset: int = 0, limit: int = 50
) -> Tuple[List[Image], int]:
    """Return a page of images and the total count for the user."""
    base = db.query(Image).filter(Image.user_id == user_id)
    total = base.count()
    items = base.order_by(Image.id.desc()).offset(offset).limit(limit).all()
    return items, total


def get_all_images_with_containers(
    db: Session, user_id: int, offset: int = 0, limit: int = 50
) -> Tuple[List[Image], int]:
    """Return a page of images (with containers eager-loaded) and the total count."""
    base = db.query(Image).filter(Image.user_id == user_id)
    total = base.count()
    items = (
        base.options(joinedload(Image.containers))
        .order_by(Image.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def get_by_app_hostname(
    db: Session, app_hostname: str, user_id: int
) -> Optional[Image]:
    """Get image by app_hostname for a specific user"""
    return (
        db.query(Image)
        .filter(Image.app_hostname == app_hostname)
        .filter(Image.user_id == user_id)
        .first()
    )
