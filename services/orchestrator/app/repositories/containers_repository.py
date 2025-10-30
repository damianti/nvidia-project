from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.models import Container


def create(db: Session, container: Container) -> Container:
    db.add(container)
    return container


def get_by_id_and_user(db: Session, container_id: int, user_id: int) -> Optional[Container]:
    return db.query(Container)\
        .filter(Container.user_id == user_id)\
        .filter(Container.id == container_id)\
        .first()


def get_containers_by_image_id(db: Session, image_id: int) -> List[Container]:
    return db.query(Container).filter(Container.image_id == image_id).all()


def list_by_user(db: Session, user_id: int) -> List[Container]:
    return db.query(Container).filter(Container.user_id == user_id).all()


def list_by_image_and_user(db: Session, image_id: int, user_id: int) -> List[Container]:
    return db.query(Container)\
        .filter(Container.image_id == image_id)\
        .filter(Container.user_id == user_id)\
        .all()