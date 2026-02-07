from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class EmailCredential(Base):
    """Stores encrypted email credentials for package scanning."""

    __tablename__ = "email_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # IMAP settings
    imap_server = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)
    email_address = Column(String(255), nullable=False)
    encrypted_password = Column(String(500), nullable=False)  # Encrypted with Fernet

    # Auto-scan settings
    enabled = Column(Boolean, default=True, nullable=False)
    scan_interval_hours = Column(Integer, default=1, nullable=False)  # How often to scan
    days_to_scan = Column(Integer, default=30, nullable=False)  # How many days back to look

    # Tracking
    last_scan_at = Column(DateTime, nullable=True)
    last_scan_status = Column(String(50), nullable=True)  # "success", "error"
    last_scan_message = Column(String(500), nullable=True)
    packages_found_last_scan = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="email_credential")
