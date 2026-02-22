from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CustomWidgetData(Base):
    __tablename__ = "custom_widget_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    widget_id = Column(String(50), nullable=False)  # e.g. "widget-1234567890"

    # Display
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255))
    description = Column(Text)
    icon = Column(String(50))  # emoji e.g. "✅", "⚠️"

    # Link
    link_url = Column(Text)
    link_text = Column(String(100))

    # Visibility
    visible = Column(Boolean, default=True)

    # Alert
    alert_active = Column(Boolean, default=False)
    alert_severity = Column(String(20))  # 'critical', 'warning', 'info'
    alert_message = Column(String(255))
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)

    # Styling
    highlight = Column(Boolean, default=False)
    color = Column(String(20))  # 'red', 'yellow', 'green', 'blue'

    # Ordering
    priority = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("idx_custom_widget_items", "user_id", "widget_id", "visible"),
        Index("idx_custom_widget_alerts", "user_id", "alert_active"),
    )
