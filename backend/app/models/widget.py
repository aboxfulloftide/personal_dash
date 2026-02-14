from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    widget_type = Column(String(50), nullable=False)
    config = Column(JSON)
    layout = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Alert system fields
    alert_active = Column(Boolean, default=False)
    alert_severity = Column(String(20))  # 'critical', 'warning', 'info'
    alert_message = Column(Text)
    alert_triggered_at = Column(DateTime)
    original_layout_x = Column(Integer)
    original_layout_y = Column(Integer)

    user = relationship("User", back_populates="widget_configs")


class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    layout = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="dashboard_layouts")
