from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class NetworkStatus(Base):
    __tablename__ = "network_status"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)  # online, degraded, offline
    ip_address = Column(String(45), nullable=True)
    isp = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_network_status_user_timestamp', 'user_id', 'timestamp'),
    )


class NetworkPingResult(Base):
    __tablename__ = "network_ping_results"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_host = Column(String(255), nullable=False)
    target_name = Column(String(100), nullable=True)
    latency_ms = Column(Float, nullable=True)
    jitter_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, nullable=True)
    is_reachable = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_ping_user_timestamp', 'user_id', 'timestamp'),
    )
