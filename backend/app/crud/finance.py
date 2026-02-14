from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from app.models.finance import StockQuote, CryptoPrice
from collections import defaultdict


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


# =============================================================================
# Portfolio History Calculation
# =============================================================================

def calculate_portfolio_history(
    db: Session,
    holdings: list[dict],
    days: int,
    is_crypto: bool = False
) -> dict:
    """
    Calculate portfolio value over time.

    Args:
        db: Database session
        holdings: List of dicts with {symbol/coin: str, shares/amount: float}
        days: Number of days of history to fetch
        is_crypto: Whether this is crypto (True) or stocks (False)

    Returns:
        dict with data_points, start_date, end_date, current_value, etc.
    """
    if not holdings:
        return {
            "data_points": [],
            "start_date": "",
            "end_date": "",
            "current_value": 0.0,
            "starting_value": 0.0,
            "total_gain_loss_pct": 0.0,
            "display_mode": "daily"
        }

    # Determine cutoff date and display mode
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    display_mode = "weekly" if days > 30 else "daily"

    # Extract symbols/coins and create holdings map
    if is_crypto:
        identifiers = [h.get("coin") or h.get("coin_id") for h in holdings]
        holdings_map = {(h.get("coin") or h.get("coin_id")): h.get("amount", 0) for h in holdings}
        Model = CryptoPrice
        id_field = CryptoPrice.coin_id
    else:
        identifiers = [h["symbol"] for h in holdings]
        holdings_map = {h["symbol"]: h.get("shares", 0) for h in holdings}
        Model = StockQuote
        id_field = StockQuote.symbol

    # Query all historical prices for these symbols/coins
    # Get the last price of each day for each symbol/coin
    result = db.execute(
        select(
            id_field,
            func.DATE(Model.recorded_at).label('date'),
            Model.price,
            Model.recorded_at
        )
        .where(
            id_field.in_(identifiers),
            Model.recorded_at >= cutoff,
            Model.price.isnot(None)
        )
        .order_by(Model.recorded_at.asc())
    )

    rows = result.all()

    if not rows:
        return {
            "data_points": [],
            "start_date": "",
            "end_date": "",
            "current_value": 0.0,
            "starting_value": 0.0,
            "total_gain_loss_pct": 0.0,
            "display_mode": display_mode
        }

    # Group prices by date and symbol/coin - keep last price of each day
    daily_prices = defaultdict(dict)  # {date_str: {symbol: price}}

    for identifier, date, price, recorded_at in rows:
        date_str = str(date)
        # Keep updating - last one wins (most recent price of the day)
        daily_prices[date_str][identifier] = price

    # Forward-fill missing prices
    sorted_dates = sorted(daily_prices.keys())
    last_known_prices = {}

    for date_str in sorted_dates:
        for identifier in identifiers:
            if identifier in daily_prices[date_str]:
                last_known_prices[identifier] = daily_prices[date_str][identifier]
            elif identifier in last_known_prices:
                daily_prices[date_str][identifier] = last_known_prices[identifier]

    # Calculate portfolio value for each date (only dates where all holdings have prices)
    portfolio_values = []
    for date_str in sorted_dates:
        # Skip if not all holdings have prices for this date
        if not all(identifier in daily_prices[date_str] for identifier in identifiers):
            continue

        total_value = sum(
            daily_prices[date_str][identifier] * holdings_map[identifier]
            for identifier in identifiers
        )
        portfolio_values.append((date_str, total_value))

    if not portfolio_values:
        return {
            "data_points": [],
            "start_date": "",
            "end_date": "",
            "current_value": 0.0,
            "starting_value": 0.0,
            "total_gain_loss_pct": 0.0,
            "display_mode": display_mode
        }

    # Aggregate to weekly if needed
    if display_mode == "weekly":
        weekly_values = []
        i = 0
        while i < len(portfolio_values):
            # Take first value of each week (every 7 days)
            weekly_values.append(portfolio_values[i])
            i += 7
        # Always include the last value if not already included
        if portfolio_values[-1] not in weekly_values:
            weekly_values.append(portfolio_values[-1])
        portfolio_values = weekly_values

    # Calculate percentage changes
    starting_value = portfolio_values[0][1]
    data_points = []

    for date_str, total_value in portfolio_values:
        percentage_change = ((total_value - starting_value) / starting_value * 100) if starting_value else 0
        data_points.append({
            "date": date_str,
            "total_value": round(total_value, 2),
            "percentage_change": round(percentage_change, 2)
        })

    current_value = portfolio_values[-1][1]
    total_gain_loss_pct = ((current_value - starting_value) / starting_value * 100) if starting_value else 0

    return {
        "data_points": data_points,
        "start_date": portfolio_values[0][0],
        "end_date": portfolio_values[-1][0],
        "current_value": round(current_value, 2),
        "starting_value": round(starting_value, 2),
        "total_gain_loss_pct": round(total_gain_loss_pct, 2),
        "display_mode": display_mode
    }
