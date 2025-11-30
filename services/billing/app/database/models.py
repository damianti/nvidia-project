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
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    status: Mapped[BillingStatus] = mapped_column(Enum(BillingStatus, name="billing_status_enum"), nullable=False, default=BillingStatus.ACTIVE)
    