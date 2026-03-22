from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

ACCESS_LEVELS = ("none", "viewer", "user", "admin")
ACCESS_LEVEL_RANK = {level: i for i, level in enumerate(ACCESS_LEVELS)}


class App(Base):
    __tablename__ = "apps"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user_access = relationship("UserAppAccess", back_populates="app", cascade="all, delete-orphan")


class UserAppAccess(Base):
    __tablename__ = "user_app_access"
    __table_args__ = (UniqueConstraint("user_id", "app_id", name="uq_user_app"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    app_id = Column(Integer, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(16), nullable=False, default="viewer")
    granted_at = Column(DateTime, server_default=func.now())

    app = relationship("App", back_populates="user_access")
    user = relationship("User", back_populates="app_access")
