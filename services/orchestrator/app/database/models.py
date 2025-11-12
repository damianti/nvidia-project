import os
import psycopg2
import enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Enum
from datetime import datetime
from typing import List, Optional


class PortStatus(enum.Enum):
    FREE = "free"
    ASSIGNED = "assigned"
    RESERVED = "reserved"

class ContainerStatus(enum.Enum):
    RUNNING = "running"
    STOPPED = "stopped"


class Base(DeclarativeBase):
    pass

class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    website_url: Mapped[str] = mapped_column(String(255), nullable=False)
    min_instances: Mapped[int] = mapped_column(Integer, default=1)
    max_instances: Mapped[int] = mapped_column(Integer, default=3)
    cpu_limit: Mapped[str] = mapped_column(String(50), default="0.5")
    memory_limit: Mapped[str] = mapped_column(String(50), default="512m")
    status: Mapped[str] = mapped_column(String(50), default="registered")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationship with containers
    containers: Mapped[List["Container"]] = relationship(back_populates="image")
    

class Container(Base):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    container_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    internal_port: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    external_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(Enum(ContainerStatus, name="container_status_enum"), default=ContainerStatus.RUNNING)
    cpu_usage: Mapped[str] = mapped_column(String(50), default="0.0")
    memory_usage: Mapped[str] = mapped_column(String(50), default="0m")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationship with images
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    image: Mapped["Image"] = relationship(back_populates="containers")



class Billing(Base):
    __tablename__ = "billings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)