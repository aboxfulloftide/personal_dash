# Task 013: Stock & Crypto Widgets

## Objective
Build widgets for tracking stocks and cryptocurrency prices using free APIs.

## Prerequisites
- Task 006 completed (Widget Framework)
- Task 003 completed (Database Schema)

## Features

### Stock Widget
- Track multiple stock symbols
- Current price and daily change
- Sparkline mini-charts
- Market status indicator (open/closed)
- Support for major exchanges

### Crypto Widget
- Track multiple cryptocurrencies
- Current price in USD
- 24h change percentage
- Market cap display
- Mini price charts

## API Choices

### Stocks: Yahoo Finance (via yfinance library)
- **Free**: No API key required
- **Reliable**: Widely used
- **Data**: Real-time quotes, historical data

### Crypto: CoinGecko API
- **Free tier**: 10-30 calls/minute
- **No API key** for basic usage
- **Comprehensive**: 10,000+ coins

## Deliverables

### 1. Database Models

#### backend/app/models/finance.py:
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class AssetType(enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    asset_type = Column(Enum(AssetType), nullable=False)
    symbol = Column(String(20), nullable=False)  # e.g., "AAPL" or "bitcoin"
    display_name = Column(String(100), nullable=True)  # e.g., "Apple Inc." or "Bitcoin"

    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")


class PriceCache(Base):
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, index=True)

    asset_type = Column(Enum(AssetType), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)

    current_price = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    change_amount = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)

    high_24h = Column(Float, nullable=True)
    low_24h = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)

    # Sparkline data (JSON string of prices)
    sparkline_data = Column(String(2000), nullable=True)

    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
```

### 2. Stock Service

#### backend/app/services/stock_service.py:
```python
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from sqlalchemy.orm import Session
from app.models.finance import WatchlistItem, PriceCache, AssetType


class StockService:
    """Stock data service using Yahoo Finance."""

    CACHE_DURATION = timedelta(minutes=5)  # Cache for 5 minutes during market hours

    def __init__(self):
        pass

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current stock quote."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            previous_close = info.get('previousClose', 0)

            change = current_price - previous_close if current_price and previous_close else 0
            change_percent = (change / previous_close * 100) if previous_close else 0

            return {
                "symbol": symbol.upper(),
                "name": info.get('shortName', symbol),
                "current_price": round(current_price, 2) if current_price else None,
                "previous_close": round(previous_close, 2) if previous_close else None,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "high": info.get('dayHigh'),
                "low": info.get('dayLow'),
                "volume": info.get('volume'),
                "market_cap": info.get('marketCap'),
                "exchange": info.get('exchange'),
                "currency": info.get('currency', 'USD'),
                "market_state": info.get('marketState', 'CLOSED'),
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "symbol": symbol.upper(),
                "error": str(e)
            }

    def get_sparkline(self, symbol: str, period: str = "5d") -> List[float]:
        """Get price history for sparkline chart."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1h")

            if hist.empty:
                return []

            # Return closing prices
            prices = hist['Close'].tolist()
            return [round(p, 2) for p in prices[-50:]]  # Last 50 data points
        except Exception:
            return []

    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get quotes for multiple symbols."""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_quote(symbol)
        return results

    def search_symbol(self, query: str) -> List[Dict[str, Any]]:
        """Search for stock symbols."""
        try:
            ticker = yf.Ticker(query)
            info = ticker.info

            if info.get('symbol'):
                return [{
                    "symbol": info.get('symbol'),
                    "name": info.get('shortName', info.get('longName', '')),
                    "exchange": info.get('exchange'),
                    "type": "stock"
                }]
            return []
        except Exception:
            return []

    def is_market_open(self) -> bool:
        """Check if US stock market is currently open."""
        now = datetime.utcnow()
        # Simple check: Mon-Fri, 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
        if now.weekday() >= 5:  # Weekend
            return False

        # Rough UTC hours for market open
        hour = now.hour
        return 14 <= hour < 21


class StockCacheService:
    """Stock service with caching layer."""

    def __init__(self):
        self.stock_service = StockService()
        self.cache_duration = timedelta(minutes=5)

    def get_cached_quote(
        self, 
        db: Session, 
        symbol: str, 
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get stock quote with caching."""

        symbol = symbol.upper()

        # Check cache
        if not force_refresh:
            cache = db.query(PriceCache).filter(
                PriceCache.asset_type == AssetType.STOCK,
                PriceCache.symbol == symbol,
                PriceCache.expires_at > datetime.utcnow()
            ).first()

            if cache:
                return {
                    "symbol": symbol,
                    "current_price": cache.current_price,
                    "previous_close": cache.previous_close,
                    "change": cache.change_amount,
                    "change_percent": cache.change_percent,
                    "high": cache.high_24h,
                    "low": cache.low_24h,
                    "volume": cache.volume,
                    "market_cap": cache.market_cap,
                    "sparkline": json.loads(cache.sparkline_data) if cache.sparkline_data else [],
                    "cached": True,
                    "cached_at": cache.cached_at.isoformat()
                }

        # Fetch fresh data
        quote = self.stock_service.get_quote(symbol)

        if "error" not in quote:
            sparkline = self.stock_service.get_sparkline(symbol)
            quote["sparkline"] = sparkline

            # Update cache
            cache = db.query(PriceCache).filter(
                PriceCache.asset_type == AssetType.STOCK,
                PriceCache.symbol == symbol
            ).first()

            if not cache:
                cache = PriceCache(
                    asset_type=AssetType.STOCK,
                    symbol=symbol
                )
                db.add(cache)

            cache.current_price = quote.get("current_price")
            cache.previous_close = quote.get("previous_close")
            cache.change_amount = quote.get("change")
            cache.change_percent = quote.get("change_percent")
            cache.high_24h = quote.get("high")
            cache.low_24h = quote.get("low")
            cache.volume = quote.get("volume")
            cache.market_cap = quote.get("market_cap")
            cache.sparkline_data = json.dumps(sparkline)
            cache.cached_at = datetime.utcnow()
            cache.expires_at = datetime.utcnow() + self.cache_duration

            db.commit()

        quote["cached"] = False
        return quote
```

### 3. Crypto Service

#### backend/app/services/crypto_service.py:
```python
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

from sqlalchemy.orm import Session
from app.models.finance import PriceCache, AssetType


class CoinGeckoService:
    """Crypto data service using CoinGecko API."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Common crypto ID mappings
    SYMBOL_TO_ID = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "SOL": "solana",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LTC": "litecoin",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "ATOM": "cosmos",
    }

    def __init__(self):
        self.cache_duration = timedelta(minutes=2)  # Crypto is more volatile

    async def get_price(self, coin_id: str) -> Dict[str, Any]:
        """Get current price for a cryptocurrency."""

        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
            "include_last_updated_at": "true"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/simple/price",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

        if coin_id not in data:
            return {"error": f"Coin {coin_id} not found"}

        coin_data = data[coin_id]

        return {
            "id": coin_id,
            "current_price": coin_data.get("usd"),
            "change_24h": coin_data.get("usd_24h_change"),
            "volume_24h": coin_data.get("usd_24h_vol"),
            "market_cap": coin_data.get("usd_market_cap"),
            "last_updated": coin_data.get("last_updated_at"),
            "fetched_at": datetime.utcnow().isoformat()
        }

    async def get_multiple_prices(self, coin_ids: List[str]) -> Dict[str, Dict]:
        """Get prices for multiple cryptocurrencies."""

        ids_str = ",".join(coin_ids)

        params = {
            "ids": ids_str,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
            "include_sparkline": "true",
            "sparkline": "true"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ids_str,
                    "sparkline": "true",
                    "price_change_percentage": "24h"
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

        results = {}
        for coin in data:
            results[coin["id"]] = {
                "id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "current_price": coin.get("current_price"),
                "change_24h": coin.get("price_change_percentage_24h"),
                "high_24h": coin.get("high_24h"),
                "low_24h": coin.get("low_24h"),
                "volume_24h": coin.get("total_volume"),
                "market_cap": coin.get("market_cap"),
                "sparkline": coin.get("sparkline_in_7d", {}).get("price", []),
                "image": coin.get("image")
            }

        return results

    async def search_coin(self, query: str) -> List[Dict[str, Any]]:
        """Search for cryptocurrencies."""

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search",
                params={"query": query},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for coin in data.get("coins", [])[:10]:
            results.append({
                "id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "thumb": coin.get("thumb"),
                "market_cap_rank": coin.get("market_cap_rank")
            })

        return results

    def symbol_to_id(self, symbol: str) -> str:
        """Convert common symbol to CoinGecko ID."""
        return self.SYMBOL_TO_ID.get(symbol.upper(), symbol.lower())


class CryptoCacheService:
    """Crypto service with caching layer."""

    def __init__(self):
        self.api = CoinGeckoService()
        self.cache_duration = timedelta(minutes=2)

    async def get_cached_prices(
        self, 
        db: Session, 
        coin_ids: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Dict]:
        """Get crypto prices with caching."""

        results = {}
        ids_to_fetch = []

        # Check cache for each coin
        if not force_refresh:
            for coin_id in coin_ids:
                cache = db.query(PriceCache).filter(
                    PriceCache.asset_type == AssetType.CRYPTO,
                    PriceCache.symbol == coin_id,
                    PriceCache.expires_at > datetime.utcnow()
                ).first()

                if cache:
                    results[coin_id] = {
                        "id": coin_id,
                        "current_price": cache.current_price,
                        "change_24h": cache.change_percent,
                        "high_24h": cache.high_24h,
                        "low_24h": cache.low_24h,
                        "volume_24h": cache.volume,
                        "market_cap": cache.market_cap,
                        "sparkline": json.loads(cache.sparkline_data) if cache.sparkline_data else [],
                        "cached": True
                    }
                else:
                    ids_to_fetch.append(coin_id)
        else:
            ids_to_fetch = coin_ids

        # Fetch missing data
        if ids_to_fetch:
            fresh_data = await self.api.get_multiple_prices(ids_to_fetch)

            for coin_id, data in fresh_data.items():
                # Update cache
                cache = db.query(PriceCache).filter(
                    PriceCache.asset_type == AssetType.CRYPTO,
                    PriceCache.symbol == coin_id
                ).first()

                if not cache:
                    cache = PriceCache(
                        asset_type=AssetType.CRYPTO,
                        symbol=coin_id
                    )
                    db.add(cache)

                cache.current_price = data.get("current_price")
                cache.change_percent = data.get("change_24h")
                cache.high_24h = data.get("high_24h")
                cache.low_24h = data.get("low_24h")
                cache.volume = data.get("volume_24h")
                cache.market_cap = data.get("market_cap")
                cache.sparkline_data = json.dumps(data.get("sparkline", [])[-50:])
                cache.cached_at = datetime.utcnow()
                cache.expires_at = datetime.utcnow() + self.cache_duration

                data["cached"] = False
                results[coin_id] = data

            db.commit()

        return results
```

### 4. API Endpoints

#### backend/app/api/v1/finance.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.finance import WatchlistItem, AssetType
from app.schemas.finance import (
    WatchlistItemCreate, WatchlistItemResponse,
    StockQuoteResponse, CryptoQuoteResponse, SearchResult
)
from app.api.deps import get_current_user
from app.services.stock_service import StockCacheService
from app.services.crypto_service import CryptoCacheService, CoinGeckoService

router = APIRouter(prefix="/finance", tags=["finance"])
stock_service = StockCacheService()
crypto_service = CryptoCacheService()


# ============ Watchlist Endpoints ============

@router.get("/watchlist", response_model=List[WatchlistItemResponse])
async def get_watchlist(
    asset_type: Optional[AssetType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's watchlist items."""
    query = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id
    )

    if asset_type:
        query = query.filter(WatchlistItem.asset_type == asset_type)

    return query.order_by(WatchlistItem.display_order).all()


@router.post("/watchlist", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    item: WatchlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add item to watchlist."""
    # Check limit (max 20 items per type)
    count = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.asset_type == item.asset_type
    ).count()

    if count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 20 {item.asset_type.value} items allowed"
        )

    # Check for duplicate
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.asset_type == item.asset_type,
        WatchlistItem.symbol == item.symbol.upper()
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item already in watchlist"
        )

    watchlist_item = WatchlistItem(
        user_id=current_user.id,
        asset_type=item.asset_type,
        symbol=item.symbol.upper() if item.asset_type == AssetType.STOCK else item.symbol.lower(),
        display_name=item.display_name,
        display_order=count
    )

    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    return watchlist_item


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove item from watchlist."""
    item = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()


# ============ Stock Endpoints ============

@router.get("/stocks/quote/{symbol}", response_model=StockQuoteResponse)
async def get_stock_quote(
    symbol: str,
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get stock quote."""
    quote = stock_service.get_cached_quote(db, symbol, force_refresh=refresh)

    if "error" in quote:
        raise HTTPException(status_code=404, detail=quote["error"])

    return quote


@router.get("/stocks/watchlist")
async def get_stock_watchlist_quotes(
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quotes for all stocks in watchlist."""
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.asset_type == AssetType.STOCK
    ).order_by(WatchlistItem.display_order).all()

    results = []
    for item in items:
        quote = stock_service.get_cached_quote(db, item.symbol, force_refresh=refresh)
        quote["watchlist_id"] = item.id
        quote["display_name"] = item.display_name
        results.append(quote)

    return results


@router.get("/stocks/market-status")
async def get_market_status(
    current_user: User = Depends(get_current_user)
):
    """Check if US stock market is open."""
    from app.services.stock_service import StockService
    service = StockService()
    return {"is_open": service.is_market_open()}


# ============ Crypto Endpoints ============

@router.get("/crypto/quote/{coin_id}", response_model=CryptoQuoteResponse)
async def get_crypto_quote(
    coin_id: str,
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get crypto quote."""
    results = await crypto_service.get_cached_prices(db, [coin_id], force_refresh=refresh)

    if coin_id not in results:
        raise HTTPException(status_code=404, detail="Coin not found")

    return results[coin_id]


@router.get("/crypto/watchlist")
async def get_crypto_watchlist_quotes(
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quotes for all crypto in watchlist."""
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.asset_type == AssetType.CRYPTO
    ).order_by(WatchlistItem.display_order).all()

    if not items:
        return []

    coin_ids = [item.symbol for item in items]
    results = await crypto_service.get_cached_prices(db, coin_ids, force_refresh=refresh)

    watchlist_results = []
    for item in items:
        if item.symbol in results:
            data = results[item.symbol]
            data["watchlist_id"] = item.id
            data["display_name"] = item.display_name
            watchlist_results.append(data)

    return watchlist_results


@router.get("/crypto/search", response_model=List[SearchResult])
async def search_crypto(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """Search for cryptocurrencies."""
    if len(q) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters"
        )

    api = CoinGeckoService()
    results = await api.search_coin(q)
    return results
```

### 5. Pydantic Schemas

#### backend/app/schemas/finance.py:
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AssetTypeEnum(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"


class WatchlistItemCreate(BaseModel):
    asset_type: AssetTypeEnum
    symbol: str = Field(..., min_length=1, max_length=20)
    display_name: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    id: int
    asset_type: AssetTypeEnum
    symbol: str
    display_name: Optional[str]
    display_order: int

    class Config:
        from_attributes = True


class StockQuoteResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    current_price: Optional[float]
    previous_close: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
    high: Optional[float]
    low: Optional[float]
    volume: Optional[int]
    market_cap: Optional[int]
    sparkline: List[float] = []
    cached: bool = False

    watchlist_id: Optional[int] = None
    display_name: Optional[str] = None


class CryptoQuoteResponse(BaseModel):
    id: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    current_price: Optional[float]
    change_24h: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    volume_24h: Optional[float]
    market_cap: Optional[float]
    sparkline: List[float] = []
    image: Optional[str] = None
    cached: bool = False

    watchlist_id: Optional[int] = None
    display_name: Optional[str] = None


class SearchResult(BaseModel):
    id: str
    symbol: str
    name: str
    thumb: Optional[str] = None
    market_cap_rank: Optional[int] = None
```

### 6. Frontend Stock Widget

#### frontend/src/components/widgets/StockWidget.jsx:
```jsx
import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Plus, X, Search } from 'lucide-react';
import { useStocks } from '../../hooks/useStocks';
import Sparkline from '../common/Sparkline';

export default function StockWidget({ config }) {
  const { 
    stocks, 
    loading, 
    marketOpen,
    refreshStocks, 
    addStock, 
    removeStock,
    searchStock 
  } = useStocks();

  const [showAdd, setShowAdd] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const formatPrice = (price) => {
    if (!price) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  };

  const formatChange = (change, percent) => {
    if (change === null || change === undefined) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${percent?.toFixed(2)}%)`;
  };

  const handleAddStock = async (symbol) => {
    await addStock(symbol);
    setShowAdd(false);
    setSearchQuery('');
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-medium">Stocks</span>
          <span className={`text-xs px-2 py-0.5 rounded ${
            marketOpen ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {marketOpen ? 'Market Open' : 'Market Closed'}
          </span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => refreshStocks(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAdd(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Add Stock"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stock List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {stocks.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No stocks in watchlist</p>
            <button
              onClick={() => setShowAdd(true)}
              className="mt-2 text-blue-500 hover:underline"
            >
              Add your first stock
            </button>
          </div>
        ) : (
          stocks.map((stock) => (
            <StockRow 
              key={stock.watchlist_id || stock.symbol} 
              stock={stock}
              onRemove={() => removeStock(stock.watchlist_id)}
            />
          ))
        )}
      </div>

      {/* Add Stock Modal */}
      {showAdd && (
        <AddStockModal
          onAdd={handleAddStock}
          onClose={() => setShowAdd(false)}
        />
      )}
    </div>
  );
}

function StockRow({ stock, onRemove }) {
  const isPositive = (stock.change || 0) >= 0;

  return (
    <div className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg group">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium">{stock.symbol}</span>
          {stock.name && (
            <span className="text-xs text-gray-400 truncate">
              {stock.name}
            </span>
          )}
        </div>
      </div>

      {/* Sparkline */}
      {stock.sparkline?.length > 0 && (
        <div className="w-16 h-8 mx-2">
          <Sparkline 
            data={stock.sparkline} 
            color={isPositive ? '#22c55e' : '#ef4444'}
          />
        </div>
      )}

      <div className="text-right">
        <div className="font-medium">
          ${stock.current_price?.toFixed(2) || '-'}
        </div>
        <div className={`text-xs ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? <TrendingUp className="w-3 h-3 inline" /> : <TrendingDown className="w-3 h-3 inline" />}
          {' '}{stock.change_percent?.toFixed(2)}%
        </div>
      </div>

      <button
        onClick={onRemove}
        className="ml-2 p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-200 rounded"
      >
        <X className="w-3 h-3 text-gray-400" />
      </button>
    </div>
  );
}

function AddStockModal({ onAdd, onClose }) {
  const [query, setQuery] = useState('');
  const [suggestions] = useState([
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.' },
    { symbol: 'MSFT', name: 'Microsoft Corporation' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.' },
    { symbol: 'TSLA', name: 'Tesla Inc.' },
    { symbol: 'NVDA', name: 'NVIDIA Corporation' },
  ]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Add Stock</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Enter stock symbol (e.g., AAPL)"
            value={query}
            onChange={(e) => setQuery(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && query && onAdd(query)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
            autoFocus
          />
        </div>

        {query && (
          <button
            onClick={() => onAdd(query)}
            className="w-full p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 mb-4"
          >
            Add {query}
          </button>
        )}

        <div>
          <p className="text-xs text-gray-500 mb-2">Popular stocks:</p>
          <div className="grid grid-cols-2 gap-2">
            {suggestions.map((s) => (
              <button
                key={s.symbol}
                onClick={() => onAdd(s.symbol)}
                className="text-left p-2 hover:bg-gray-50 rounded border"
              >
                <div className="font-medium">{s.symbol}</div>
                <div className="text-xs text-gray-500 truncate">{s.name}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 7. Frontend Crypto Widget

#### frontend/src/components/widgets/CryptoWidget.jsx:
```jsx
import React, { useState } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Plus, X, Search } from 'lucide-react';
import { useCrypto } from '../../hooks/useCrypto';
import Sparkline from '../common/Sparkline';

export default function CryptoWidget({ config }) {
  const { 
    cryptos, 
    loading, 
    refreshCrypto, 
    addCrypto, 
    removeCrypto,
    searchCrypto 
  } = useCrypto();

  const [showAdd, setShowAdd] = useState(false);

  const formatPrice = (price) => {
    if (!price) return '-';
    if (price < 1) {
      return `$${price.toFixed(6)}`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  const formatMarketCap = (cap) => {
    if (!cap) return '-';
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`;
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`;
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(2)}M`;
    return `$${cap.toLocaleString()}`;
  };

  const handleAddCrypto = async (coinId, name) => {
    await addCrypto(coinId, name);
    setShowAdd(false);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="font-medium">Crypto</span>
        <div className="flex gap-1">
          <button
            onClick={() => refreshCrypto(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAdd(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Add Crypto"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Crypto List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {cryptos.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No crypto in watchlist</p>
            <button
              onClick={() => setShowAdd(true)}
              className="mt-2 text-blue-500 hover:underline"
            >
              Add your first crypto
            </button>
          </div>
        ) : (
          cryptos.map((crypto) => (
            <CryptoRow 
              key={crypto.watchlist_id || crypto.id} 
              crypto={crypto}
              formatPrice={formatPrice}
              formatMarketCap={formatMarketCap}
              onRemove={() => removeCrypto(crypto.watchlist_id)}
            />
          ))
        )}
      </div>

      {/* Add Crypto Modal */}
      {showAdd && (
        <AddCryptoModal
          onAdd={handleAddCrypto}
          onSearch={searchCrypto}
          onClose={() => setShowAdd(false)}
        />
      )}
    </div>
  );
}

function CryptoRow({ crypto, formatPrice, formatMarketCap, onRemove }) {
  const isPositive = (crypto.change_24h || 0) >= 0;

  return (
    <div className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg group">
      <div className="flex items-center gap-2 flex-1 min-w-0">
        {crypto.image && (
          <img src={crypto.image} alt="" className="w-6 h-6 rounded-full" />
        )}
        <div>
          <div className="font-medium">{crypto.symbol}</div>
          <div className="text-xs text-gray-400 truncate">{crypto.name}</div>
        </div>
      </div>

      {/* Sparkline */}
      {crypto.sparkline?.length > 0 && (
        <div className="w-16 h-8 mx-2">
          <Sparkline 
            data={crypto.sparkline} 
            color={isPositive ? '#22c55e' : '#ef4444'}
          />
        </div>
      )}

      <div className="text-right">
        <div className="font-medium">{formatPrice(crypto.current_price)}</div>
        <div className={`text-xs flex items-center justify-end gap-1 ${
          isPositive ? 'text-green-600' : 'text-red-600'
        }`}>
          {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {crypto.change_24h?.toFixed(2)}%
        </div>
      </div>

      <button
        onClick={onRemove}
        className="ml-2 p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-200 rounded"
      >
        <X className="w-3 h-3 text-gray-400" />
      </button>
    </div>
  );
}

function AddCryptoModal({ onAdd, onSearch, onClose }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const popularCoins = [
    { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin' },
    { id: 'ethereum', symbol: 'ETH', name: 'Ethereum' },
    { id: 'solana', symbol: 'SOL', name: 'Solana' },
    { id: 'cardano', symbol: 'ADA', name: 'Cardano' },
    { id: 'dogecoin', symbol: 'DOGE', name: 'Dogecoin' },
    { id: 'ripple', symbol: 'XRP', name: 'XRP' },
  ];

  const handleSearch = async (q) => {
    setQuery(q);
    if (q.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const res = await onSearch(q);
      setResults(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Add Cryptocurrency</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search cryptocurrency..."
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
            autoFocus
          />
        </div>

        {/* Search Results */}
        {results.length > 0 && (
          <div className="mb-4 max-h-48 overflow-y-auto">
            {results.map((coin) => (
              <button
                key={coin.id}
                onClick={() => onAdd(coin.id, coin.name)}
                className="w-full flex items-center gap-2 p-2 hover:bg-gray-50 rounded"
              >
                {coin.thumb && (
                  <img src={coin.thumb} alt="" className="w-6 h-6 rounded-full" />
                )}
                <div className="text-left">
                  <div className="font-medium">{coin.symbol}</div>
                  <div className="text-xs text-gray-500">{coin.name}</div>
                </div>
                {coin.market_cap_rank && (
                  <span className="ml-auto text-xs text-gray-400">
                    #{coin.market_cap_rank}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Popular Coins */}
        {!query && (
          <div>
            <p className="text-xs text-gray-500 mb-2">Popular cryptocurrencies:</p>
            <div className="grid grid-cols-2 gap-2">
              {popularCoins.map((coin) => (
                <button
                  key={coin.id}
                  onClick={() => onAdd(coin.id, coin.name)}
                  className="text-left p-2 hover:bg-gray-50 rounded border"
                >
                  <div className="font-medium">{coin.symbol}</div>
                  <div className="text-xs text-gray-500">{coin.name}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 8. Sparkline Component

#### frontend/src/components/common/Sparkline.jsx:
```jsx
import React, { useMemo } from 'react';

export default function Sparkline({ data, color = '#3b82f6', width = 64, height = 32 }) {
  const path = useMemo(() => {
    if (!data || data.length < 2) return '';

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data, width, height]);

  if (!data || data.length < 2) {
    return <div style={{ width, height }} />;
  }

  return (
    <svg width={width} height={height} className="overflow-visible">
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
```

### 9. React Hooks

#### frontend/src/hooks/useStocks.js:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useStocks() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [marketOpen, setMarketOpen] = useState(false);

  const fetchStocks = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      const params = forceRefresh ? '?refresh=true' : '';
      const response = await api.get(`/finance/stocks/watchlist${params}`);
      setStocks(response.data);
    } catch (err) {
      console.error('Failed to fetch stocks:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkMarketStatus = useCallback(async () => {
    try {
      const response = await api.get('/finance/stocks/market-status');
      setMarketOpen(response.data.is_open);
    } catch (err) {
      console.error('Failed to check market status:', err);
    }
  }, []);

  useEffect(() => {
    fetchStocks();
    checkMarketStatus();

    // Refresh every 5 minutes during market hours
    const interval = setInterval(() => {
      fetchStocks();
      checkMarketStatus();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [fetchStocks, checkMarketStatus]);

  const addStock = async (symbol) => {
    try {
      await api.post('/finance/watchlist', {
        asset_type: 'stock',
        symbol: symbol.toUpperCase()
      });
      await fetchStocks(true);
    } catch (err) {
      throw err;
    }
  };

  const removeStock = async (watchlistId) => {
    try {
      await api.delete(`/finance/watchlist/${watchlistId}`);
      setStocks(prev => prev.filter(s => s.watchlist_id !== watchlistId));
    } catch (err) {
      throw err;
    }
  };

  return {
    stocks,
    loading,
    marketOpen,
    refreshStocks: fetchStocks,
    addStock,
    removeStock
  };
}
```

#### frontend/src/hooks/useCrypto.js:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useCrypto() {
  const [cryptos, setCryptos] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCrypto = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      const params = forceRefresh ? '?refresh=true' : '';
      const response = await api.get(`/finance/crypto/watchlist${params}`);
      setCryptos(response.data);
    } catch (err) {
      console.error('Failed to fetch crypto:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCrypto();

    // Refresh every 2 minutes (crypto is 24/7)
    const interval = setInterval(() => {
      fetchCrypto();
    }, 2 * 60 * 1000);

    return () => clearInterval(interval);
  }, [fetchCrypto]);

  const addCrypto = async (coinId, name) => {
    try {
      await api.post('/finance/watchlist', {
        asset_type: 'crypto',
        symbol: coinId,
        display_name: name
      });
      await fetchCrypto(true);
    } catch (err) {
      throw err;
    }
  };

  const removeCrypto = async (watchlistId) => {
    try {
      await api.delete(`/finance/watchlist/${watchlistId}`);
      setCryptos(prev => prev.filter(c => c.watchlist_id !== watchlistId));
    } catch (err) {
      throw err;
    }
  };

  const searchCrypto = async (query) => {
    try {
      const response = await api.get(`/finance/crypto/search?q=${encodeURIComponent(query)}`);
      return response.data;
    } catch (err) {
      return [];
    }
  };

  return {
    cryptos,
    loading,
    refreshCrypto: fetchCrypto,
    addCrypto,
    removeCrypto,
    searchCrypto
  };
}
```

## Unit Tests

### tests/test_finance_services.py:
```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.stock_service import StockService
from app.services.crypto_service import CoinGeckoService

class TestStockService:
    def test_market_open_weekend(self):
        service = StockService()

        # Mock weekend
        with patch('app.services.stock_service.datetime') as mock_dt:
            mock_dt.utcnow.return_value = MagicMock(weekday=lambda: 6, hour=15)
            assert service.is_market_open() == False

    def test_market_open_weekday_during_hours(self):
        service = StockService()

        with patch('app.services.stock_service.datetime') as mock_dt:
            mock_dt.utcnow.return_value = MagicMock(weekday=lambda: 2, hour=16)
            assert service.is_market_open() == True

class TestCoinGeckoService:
    def test_symbol_to_id_mapping(self):
        service = CoinGeckoService()

        assert service.symbol_to_id('BTC') == 'bitcoin'
        assert service.symbol_to_id('ETH') == 'ethereum'
        assert service.symbol_to_id('unknown') == 'unknown'

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_coin(self, mock_get):
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "coins": [
                {
                    "id": "bitcoin",
                    "symbol": "btc",
                    "name": "Bitcoin",
                    "thumb": "https://example.com/btc.png",
                    "market_cap_rank": 1
                }
            ]
        }
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        service = CoinGeckoService()
        results = await service.search_coin("bitcoin")

        assert len(results) == 1
        assert results[0]["id"] == "bitcoin"
        assert results[0]["symbol"] == "BTC"
```

## Dependencies to Add

### backend/requirements.txt (additions):
```
yfinance>=0.2.0
```

## Acceptance Criteria
- [ ] Stock widget displays watchlist with prices
- [ ] Stock sparkline charts render correctly
- [ ] Market open/closed status shown
- [ ] Add/remove stocks from watchlist
- [ ] Crypto widget displays watchlist with prices
- [ ] Crypto 24h change percentage shown
- [ ] Crypto search works via CoinGecko
- [ ] Add/remove crypto from watchlist
- [ ] Data cached appropriately (5 min stocks, 2 min crypto)
- [ ] Manual refresh bypasses cache
- [ ] Max 20 items per watchlist type
- [ ] Unit tests pass

## Notes
- yfinance may have rate limits; implement backoff if needed
- CoinGecko free tier: ~10-30 calls/minute
- Consider WebSocket for real-time updates in future
- Sparklines use last 50 data points

## Estimated Time
3-4 hours

## Next Task
Task 014: Calendar Widget
