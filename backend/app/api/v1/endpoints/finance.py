import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.deps import CurrentActiveUser

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
    provider: str = Query("alphavantage", description="API provider"),
    api_key: str | None = Query(None, description="Optional API key"),
):
    """Fetch stock quotes from external API."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    quotes = []
    for symbol in symbol_list[:10]:  # Limit to 10 symbols
        try:
            if provider == "finnhub":
                quote = await fetch_finnhub(symbol, api_key or "")
            else:  # alphavantage default
                quote = await fetch_alphavantage(symbol, api_key or ALPHAVANTAGE_DEMO_KEY)
            quotes.append(quote)
        except Exception:
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
):
    """Fetch crypto prices from external API."""
    coin_list = [c.strip().lower() for c in coins.split(",") if c.strip()]
    if not coin_list:
        raise HTTPException(status_code=400, detail="No coins provided")

    try:
        if provider == "coincap":
            prices = await fetch_coincap(coin_list[:10], currency)
        else:  # coingecko default
            prices = await fetch_coingecko(coin_list[:10], currency)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch prices: {str(e)}")

    return CryptoResponse(prices=prices)
