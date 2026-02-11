from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.finance import StockQuote, CryptoPrice


# =============================================================================
# Stock Quotes
# =============================================================================

def get_latest_stock_quote(db: Session, symbol: str) -> StockQuote | None:
    """Get the most recent price for a symbol."""
    result = db.execute(
        select(StockQuote)
        .where(StockQuote.symbol == symbol)
        .order_by(desc(StockQuote.recorded_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def get_latest_stock_quotes(db: Session, symbols: list[str]) -> dict[str, StockQuote]:
    """Get the most recent price for multiple symbols."""
    results = {}
    for symbol in symbols:
        quote = get_latest_stock_quote(db, symbol)
        if quote:
            results[symbol] = quote
    return results


def create_stock_quote(
    db: Session,
    symbol: str,
    price: float | None,
    change_percent: float | None,
    provider: str
) -> StockQuote:
    """Store a new stock quote."""
    quote = StockQuote(
        symbol=symbol,
        price=price,
        change_percent=change_percent,
        provider=provider
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def get_stock_history(
    db: Session,
    symbol: str,
    days: int = 30
) -> list[StockQuote]:
    """Get historical quotes for graphing (for future use)."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    result = db.execute(
        select(StockQuote)
        .where(
            StockQuote.symbol == symbol,
            StockQuote.recorded_at >= cutoff
        )
        .order_by(StockQuote.recorded_at.asc())
    )
    return list(result.scalars().all())


# =============================================================================
# Crypto Prices (similar pattern)
# =============================================================================

def get_latest_crypto_price(db: Session, coin_id: str) -> CryptoPrice | None:
    """Get the most recent price for a coin."""
    result = db.execute(
        select(CryptoPrice)
        .where(CryptoPrice.coin_id == coin_id)
        .order_by(desc(CryptoPrice.recorded_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def get_latest_crypto_prices(db: Session, coin_ids: list[str]) -> dict[str, CryptoPrice]:
    """Get the most recent price for multiple coins."""
    results = {}
    for coin_id in coin_ids:
        price = get_latest_crypto_price(db, coin_id)
        if price:
            results[coin_id] = price
    return results


def create_crypto_price(
    db: Session,
    coin_id: str,
    symbol: str,
    price: float | None,
    change_24h: float | None,
    provider: str
) -> CryptoPrice:
    """Store a new crypto price."""
    price_record = CryptoPrice(
        coin_id=coin_id,
        symbol=symbol,
        price=price,
        change_24h=change_24h,
        provider=provider
    )
    db.add(price_record)
    db.commit()
    db.refresh(price_record)
    return price_record


def get_crypto_history(
    db: Session,
    coin_id: str,
    days: int = 30
) -> list[CryptoPrice]:
    """Get historical prices for graphing (for future use)."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    result = db.execute(
        select(CryptoPrice)
        .where(
            CryptoPrice.coin_id == coin_id,
            CryptoPrice.recorded_at >= cutoff
        )
        .order_by(CryptoPrice.recorded_at.asc())
    )
    return list(result.scalars().all())
