from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta


from app.database.models import Billing

def create_usage_record(db: Session, user_id: int, image_id: int, container_id: int, start_time: datetime) -> Billing:
    db_billing = Billing(
            user_id=user_id,
            image_id=image_id,
            container_id=container_id,
            start_time=start_time
    )
    db.add(db_billing)
    db.flush()
    return db_billing

def get_active_by_container(db: Session, container_id: int) -> None:
    pass

def update_usage_record(db: Session, usage_record: Billing, end_time: datetime, duration: timedelta, cost: float) -> Billing:
    pass
def get_by_user_and_image(db: Session, user_id: int, image_id: int) -> Billing:
    pass