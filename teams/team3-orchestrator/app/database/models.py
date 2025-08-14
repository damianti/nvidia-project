import os
import psycopg2
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from datetime import datetime
from typing import List

load_dotenv()

class Base(DeclarativeBase):
    pass

class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    min_instances: Mapped[int] = mapped_column(Integer, default=1)
    max_instances: Mapped[int] = mapped_column(Integer, default=3)
    cpu_limit: Mapped[str] = mapped_column(String(50), default="0.5")
    memory_limit: Mapped[str] = mapped_column(String(50), default="512m")
    status: Mapped[str] = mapped_column(String(50), default="registered")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationship with containers
    containers: Mapped[List["Container"]] = relationship(back_populates="image")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="images")

class Container(Base):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    container_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running")
    cpu_usage: Mapped[str] = mapped_column(String(50), default="0.0")
    memory_usage: Mapped[str] = mapped_column(String(50), default="0m")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationship with image
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    image: Mapped["Image"] = relationship(back_populates="containers")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    images: Mapped[List["Image"]] = relationship(back_populates="user")
    billings: Mapped[List["Billing"]] = relationship(back_populates="user")


class Billing(Base):
    __tablename__ = "billings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="billings")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)