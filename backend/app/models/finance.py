from sqlalchemy import Column, BigInteger, String, Float, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class StockQuote(Base):
    """Historical stock price data."""
    __tablename__ = "stock_quotes"

    id = Column(BigInteger, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    provider = Column(String(20), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_stock_symbol_recorded', 'symbol', 'recorded_at'),
    )


class CryptoPrice(Base):
    """Historical crypto price data."""
    __tablename__ = "crypto_prices"

    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(10), nullable=False)
    price = Column(Float, nullable=True)
    change_24h = Column(Float, nullable=True)
    provider = Column(String(20), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_crypto_coin_recorded', 'coin_id', 'recorded_at'),
    )
