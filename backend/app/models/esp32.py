from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Esp32Device(Base):
    __tablename__ = "esp32_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scanner_host = Column(String(64), nullable=False)
    display_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
