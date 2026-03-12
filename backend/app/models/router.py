from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Router(Base):
    __tablename__ = "routers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=False)  # IP or hostname
    ssh_port = Column(Integer, default=22)
    ssh_user = Column(String(100), default="root")
    ssh_password_enc = Column(Text)   # Fernet-encrypted, nullable if using key
    ssh_key = Column(Text)            # PEM private key, nullable if using password
    poll_interval = Column(Integer, default=60)  # seconds
    script = Column(Text)             # shell commands to run on the router
    is_online = Column(Boolean, default=False)
    ping_ms = Column(Float)
    last_seen = Column(DateTime)
    last_polled = Column(DateTime)    # when we last attempted a poll
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="routers")
    poll_results = relationship("RouterPollResult", back_populates="router", cascade="all, delete-orphan")


class RouterPollResult(Base):
    __tablename__ = "router_poll_results"

    id = Column(BigInteger, primary_key=True, index=True)
    router_id = Column(Integer, ForeignKey("routers.id", ondelete="CASCADE"), nullable=False, index=True)
    is_online = Column(Boolean, default=False)
    ping_ms = Column(Float)
    script_output = Column(Text)
    recorded_at = Column(DateTime, server_default=func.now(), index=True)

    router = relationship("Router", back_populates="poll_results")
