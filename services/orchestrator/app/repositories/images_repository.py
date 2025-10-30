from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database.models import Image, User


def create(db: Session, image: Image) -> Image:
    """Persist a new Image. Does not commit; caller controls the transaction."""
    db.add(image)
    return image


def get_by_id(db: Session, image_id: int, current_user: User) -> Optional[Image]:
    return db.query(Image)\
        .filter(Image.user_id == current_user.id)\
        .filter(Image.id == image_id).first()


def get_all_images(db: Session, current_user: User):
    return db.query(Image)\
        .filter(Image.user_id == current_user.id)\
        .all()


def get_all_images_with_containers(db: Session, current_user: User):
    return db.query(Image)\
        .options(joinedload(Image.containers))\
        .filter(Image.user_id == current_user.id)\
        .all()

        
def get_by_name_tag_user(db: Session, name: str, tag: str, user_id: int) -> Optional[Image]:
    return db.query(Image)\
        .filter(Image.user_id == user_id)\
        .filter(Image.name == name)\
        .filter(Image.tag == tag)\
        .first()


