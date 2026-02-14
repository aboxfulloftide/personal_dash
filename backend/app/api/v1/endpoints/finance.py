import httpx
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser
from app.core.database import get_db
from app.crud import finance as finance_crud
from app.schemas.finance import PortfolioHistoryResponse

# Minimum time between database records (15 minutes)
# This ensures we store ~3-4 records per hour, not every API call
MIN_STORAGE_INTERVAL_MINUTES = 15

router = APIRouter(prefix="/finance", tags=["Finance"])

# Default demo keys (very limited usage)
ALPHAVANTAGE_DEMO_KEY = "demo"


class StockQuote(BaseModel):
    symbol: str
    price: float | None
    change_percent: float | None


class StockResponse(BaseModel):
    quotes: list[StockQuote]


class CryptoPrice(BaseModel):
    id: str
    symbol: str
    price: float | None
    change_24h: float | None


class CryptoResponse(BaseModel):
    prices: list[CryptoPrice]


# =============================================================================
# Stock Quotes
# =============================================================================


async def fetch_yahoo(symbol: str) -> StockQuote:
    """Fetch stock quote from Yahoo Finance (no API key required)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=10.0)
        data = resp.json()

    try:
        result = data.get("chart", {}).get("result", [])
        if not result:
            return StockQuote(symbol=symbol, price=None, change_percent=None)

        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose")

        if price and prev_close and prev_close > 0:
            change_pct = ((price - prev_close) / prev_close) * 100
        else:
            change_pct = None

        return StockQuote(symbol=symbol, price=price, change_percent=round(change_pct, 2) if change_pct else None)
    except (ValueError, TypeError, KeyError):
        return StockQuote(symbol=symbol, price=None, change_percent=None)


async def fetch_alphavantage(symbol: str, api_key: str) -> StockQuote:
    """Fetch stock quote from Alpha Vantage."""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    quote = data.get("Global Quote", {})
    if not quote:
        return StockQuote(symbol=symbol, price=None, change_percent=None)

    try:
        price = float(quote.get("05. price", 0))
        change_pct = float(quote.get("10. change percent", "0").rstrip("%"))
    except (ValueError, TypeError):
        price = None
        change_pct = None

    return StockQuote(symbol=symbol, price=price, change_percent=change_pct)


async def fetch_finnhub(symbol: str, api_key: str) -> StockQuote:
    """Fetch stock quote from Finnhub."""
    if not api_key:
        return StockQuote(symbol=symbol, price=None, change_percent=None)

    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    try:
        price = float(data.get("c", 0))  # current price
        prev_close = float(data.get("pc", 0))  # previous close
        if prev_close > 0:
            change_pct = ((price - prev_close) / prev_close) * 100
        else:
            change_pct = 0
    except (ValueError, TypeError):
        price = None
        change_pct = None

    return StockQuote(symbol=symbol, price=price, change_percent=change_pct)


@router.get("/stocks", response_model=StockResponse)
async def get_stock_quotes(
    current_user: CurrentActiveUser,
    symbols: str = Query(..., description="Comma-separated stock symbols"),
    provider: str = Query("yahoo", description="API provider"),
    api_key: str | None = Query(None, description="Optional API key"),
    db: Session = Depends(get_db),
):
    """
    Fetch stock quotes with database fallback.

    Flow:
    1. Try to fetch from external API
    2. If successful, store in DB and return
    3. If fails, query last known price from DB
    4. If no DB record, return null
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    quotes = []
    for symbol in symbol_list[:10]:  # Limit to 10 symbols
        # Step 1: Try to fetch from external API
        try:
            if provider == "finnhub":
                quote = await fetch_finnhub(symbol, api_key or "")
            elif provider == "alphavantage":
                quote = await fetch_alphavantage(symbol, api_key or ALPHAVANTAGE_DEMO_KEY)
            else:  # yahoo default
                quote = await fetch_yahoo(symbol)

            # Step 2: Store successful fetch in DB (but only if last record is old enough)
            last_quote = finance_crud.get_latest_stock_quote(db, symbol)
            should_store = True

            if last_quote and last_quote.recorded_at:
                # Don't store if we have a recent record (within 15 minutes)
                time_since_last = datetime.now() - last_quote.recorded_at
                if time_since_last < timedelta(minutes=MIN_STORAGE_INTERVAL_MINUTES):
                    should_store = False

            if should_store:
                finance_crud.create_stock_quote(
                    db=db,
                    symbol=symbol,
                    price=quote.price,
                    change_percent=quote.change_percent,
                    provider=provider
                )

            quotes.append(quote)

        except Exception as e:
            # Step 3: API failed, fallback to last known price
            last_quote = finance_crud.get_latest_stock_quote(db, symbol)

            if last_quote:
                quotes.append(StockQuote(
                    symbol=last_quote.symbol,
                    price=last_quote.price,
                    change_percent=last_quote.change_percent
                ))
            else:
                # Step 4: No data available at all
                quotes.append(StockQuote(symbol=symbol, price=None, change_percent=None))

    return StockResponse(quotes=quotes)


# =============================================================================
# Crypto Prices
# =============================================================================

CRYPTO_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "ripple": "XRP",
    "polkadot": "DOT",
    "litecoin": "LTC",
}


async def fetch_coingecko(coins: list[str], currency: str) -> list[CryptoPrice]:
    """Fetch crypto prices from CoinGecko."""
    ids = ",".join(coins)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={currency}&include_24hr_change=true"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    prices = []
    for coin in coins:
        coin_data = data.get(coin, {})
        price = coin_data.get(currency)
        change = coin_data.get(f"{currency}_24h_change")
        prices.append(CryptoPrice(
            id=coin,
            symbol=CRYPTO_SYMBOLS.get(coin, coin.upper()[:4]),
            price=price,
            change_24h=round(change, 2) if change else None,
        ))
    return prices


async def fetch_coincap(coins: list[str], currency: str) -> list[CryptoPrice]:
    """Fetch crypto prices from CoinCap."""
    prices = []
    async with httpx.AsyncClient() as client:
        for coin in coins[:10]:
            try:
                url = f"https://api.coincap.io/v2/assets/{coin}"
                resp = await client.get(url, timeout=10.0)
                data = resp.json().get("data", {})

                price_usd = float(data.get("priceUsd", 0))
                change = float(data.get("changePercent24Hr", 0))

                # CoinCap only returns USD, conversion would need another API
                # For simplicity, we just return USD price
                prices.append(CryptoPrice(
                    id=coin,
                    symbol=data.get("symbol", coin.upper()[:4]),
                    price=round(price_usd, 2) if price_usd else None,
                    change_24h=round(change, 2) if change else None,
                ))
            except Exception:
                prices.append(CryptoPrice(
                    id=coin,
                    symbol=CRYPTO_SYMBOLS.get(coin, coin.upper()[:4]),
                    price=None,
                    change_24h=None,
                ))
    return prices


@router.get("/crypto", response_model=CryptoResponse)
async def get_crypto_prices(
    current_user: CurrentActiveUser,
    coins: str = Query(..., description="Comma-separated coin IDs (e.g., bitcoin,ethereum)"),
    currency: str = Query("usd", description="Currency for prices"),
    provider: str = Query("coingecko", description="API provider"),
    api_key: str | None = Query(None, description="Optional API key (not used currently)"),
    db: Session = Depends(get_db),
):
    """
    Fetch crypto prices with database fallback.

    Flow:
    1. Try to fetch from external API
    2. If successful, store in DB and return
    3. If fails, query last known prices from DB
    4. If no DB record, return null
    """
    coin_list = [c.strip().lower() for c in coins.split(",") if c.strip()]
    if not coin_list:
        raise HTTPException(status_code=400, detail="No coins provided")

    prices = []

    # Step 1: Try to fetch from external API
    try:
        if provider == "coincap":
            api_prices = await fetch_coincap(coin_list[:10], currency)
        else:  # coingecko default
            api_prices = await fetch_coingecko(coin_list[:10], currency)

        # Step 2: Store successful fetches in DB (but only if last record is old enough)
        for price in api_prices:
            last_price = finance_crud.get_latest_crypto_price(db, price.id)
            should_store = True

            if last_price and last_price.recorded_at:
                # Don't store if we have a recent record (within 15 minutes)
                time_since_last = datetime.now() - last_price.recorded_at
                if time_since_last < timedelta(minutes=MIN_STORAGE_INTERVAL_MINUTES):
                    should_store = False

            if should_store:
                finance_crud.create_crypto_price(
                    db=db,
                    coin_id=price.id,
                    symbol=price.symbol,
                    price=price.price,
                    change_24h=price.change_24h,
                    provider=provider
                )

        prices = api_prices

    except Exception as e:
        # Step 3: API failed, fallback to last known prices
        for coin_id in coin_list[:10]:
            last_price = finance_crud.get_latest_crypto_price(db, coin_id)

            if last_price:
                prices.append(CryptoPrice(
                    id=last_price.coin_id,
                    symbol=last_price.symbol,
                    price=last_price.price,
                    change_24h=last_price.change_24h
                ))
            else:
                # Step 4: No data available at all
                prices.append(CryptoPrice(
                    id=coin_id,
                    symbol=CRYPTO_SYMBOLS.get(coin_id, coin_id.upper()[:4]),
                    price=None,
                    change_24h=None
                ))

    return CryptoResponse(prices=prices)


# =============================================================================
# Portfolio History
# =============================================================================

@router.get("/stocks/portfolio-history", response_model=PortfolioHistoryResponse)
async def get_stock_portfolio_history(
    current_user: CurrentActiveUser,
    holdings: str = Query(..., description="JSON array of holdings: [{\"symbol\": \"AAPL\", \"shares\": 10}, ...]"),
    days: int = Query(90, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db),
):
    """
    Calculate stock portfolio value over time.

    Returns daily data points for ≤30 days, weekly for >30 days.
    """
    try:
        holdings_list = json.loads(holdings)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid holdings JSON")

    if not isinstance(holdings_list, list):
        raise HTTPException(status_code=400, detail="Holdings must be a JSON array")

    result = finance_crud.calculate_portfolio_history(
        db=db,
        holdings=holdings_list,
        days=days,
        is_crypto=False
    )

    return PortfolioHistoryResponse(**result)


@router.get("/crypto/portfolio-history", response_model=PortfolioHistoryResponse)
async def get_crypto_portfolio_history(
    current_user: CurrentActiveUser,
    holdings: str = Query(..., description="JSON array of holdings: [{\"coin\": \"bitcoin\", \"amount\": 0.5}, ...]"),
    days: int = Query(90, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db),
):
    """
    Calculate crypto portfolio value over time.

    Returns daily data points for ≤30 days, weekly for >30 days.
    """
    try:
        holdings_list = json.loads(holdings)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid holdings JSON")

    if not isinstance(holdings_list, list):
        raise HTTPException(status_code=400, detail="Holdings must be a JSON array")

    result = finance_crud.calculate_portfolio_history(
        db=db,
        holdings=holdings_list,
        days=days,
        is_crypto=True
    )

    return PortfolioHistoryResponse(**result)
