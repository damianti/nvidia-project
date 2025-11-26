from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Float, Enum
from datetime import datetime, timezone
from typing import Optional
import enum


class BillingStatus(enum.Enum):
    ACTIVE='Active'
    COMPLETED='Completed'

class Base(DeclarativeBase):
    pass

class Billing(Base):
    __tablename__ = "billings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    image_id: Mapped[int] = mapped_column(Integer, nullable=False)
    container_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=None)
    cost: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(Enum(BillingStatus, name="billing_status_enum"), default=BillingStatus.ACTIVE)
    