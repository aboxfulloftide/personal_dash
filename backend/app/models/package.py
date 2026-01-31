from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tracking_number = Column(String(100), nullable=False)
    carrier = Column(String(50), nullable=False)  # usps, ups, fedex, amazon
    description = Column(String(255))
    status = Column(String(100))
    estimated_delivery = Column(Date)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime)
    source = Column(String(20), default="manual")  # manual, email
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="packages")
    events = relationship("PackageEvent", back_populates="package", cascade="all, delete-orphan")

class PackageEvent(Base):
    __tablename__ = "package_events"

    id = Column(BigInteger, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(255))
    location = Column(String(255))
    event_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    package = relationship("Package", back_populates="events")

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email_address = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # gmail, imap
    credentials_encrypted = Column(Text)  # Encrypted OAuth tokens or app passwords
    last_checked = Column(DateTime)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="email_accounts")
