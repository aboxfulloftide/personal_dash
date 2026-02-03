# Task 008: Cryptocurrency Widget

## Objective
Build the Cryptocurrency widget using CoinGecko API (free tier) to display crypto prices, changes, and market data.

## Prerequisites
- Task 007 completed
- Widget framework working

## API Information
- **API**: CoinGecko (https://www.coingecko.com/en/api)
- **Cost**: Free tier available (no API key required for basic endpoints)
- **Rate Limit**: 10-30 calls/minute on free tier
- **Documentation**: https://www.coingecko.com/en/api/documentation

## Deliverables

### 1. Backend Crypto Service

#### app/services/crypto_service.py:
```python
import httpx
from typing import Optional, List
from app.core.cache import cache_get, cache_set

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
CACHE_TTL = 120  # 2 minutes for crypto (more volatile)

# Popular coins mapping (id -> symbol)
POPULAR_COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "solana": "SOL",
    "dogecoin": "DOGE",
    "polkadot": "DOT",
    "litecoin": "LTC",
    "chainlink": "LINK"
}

async def get_coin_list() -> List[dict]:
    """Get list of supported coins."""
    cache_key = "crypto:coin_list"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE}/coins/list",
                timeout=10.0
            )

            if response.status_code != 200:
                return []

            coins = response.json()
            await cache_set(cache_key, coins, ttl=86400)  # Cache for 24 hours
            return coins
    except Exception as e:
        print(f"Error fetching coin list: {e}")
        return []

async def search_coins(query: str) -> List[dict]:
    """Search for coins by name or symbol."""
    cache_key = f"crypto:search:{query.lower()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE}/search",
                params={"query": query},
                timeout=10.0
            )

            if response.status_code != 200:
                return []

            data = response.json()
            coins = data.get("coins", [])[:10]  # Limit to 10 results

            results = [{
                "id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "thumb": coin.get("thumb")
            } for coin in coins]

            await cache_set(cache_key, results, ttl=3600)
            return results
    except Exception as e:
        print(f"Error searching coins: {e}")
        return []

async def get_coin_price(coin_id: str, currency: str = "usd") -> Optional[dict]:
    """Get current price for a single coin."""
    cache_key = f"crypto:price:{coin_id}:{currency}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": currency,
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true"
                },
                timeout=10.0
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if coin_id not in data:
                return None

            coin_data = data[coin_id]
            result = {
                "id": coin_id,
                "price": coin_data.get(currency),
                "change_24h": coin_data.get(f"{currency}_24h_change"),
                "volume_24h": coin_data.get(f"{currency}_24h_vol"),
                "market_cap": coin_data.get(f"{currency}_market_cap"),
                "currency": currency.upper()
            }

            await cache_set(cache_key, result, ttl=CACHE_TTL)
            return result
    except Exception as e:
        print(f"Error fetching coin price: {e}")
        return None

async def get_multiple_prices(coin_ids: List[str], currency: str = "usd") -> List[dict]:
    """Get prices for multiple coins."""
    if not coin_ids:
        return []

    ids_str = ",".join(coin_ids[:20])  # Limit to 20 coins
    cache_key = f"crypto:prices:{ids_str}:{currency}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={
                    "ids": ids_str,
                    "vs_currencies": currency,
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true"
                },
                timeout=10.0
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            for coin_id in coin_ids:
                if coin_id in data:
                    coin_data = data[coin_id]
                    results.append({
                        "id": coin_id,
                        "price": coin_data.get(currency),
                        "change_24h": coin_data.get(f"{currency}_24h_change"),
                        "volume_24h": coin_data.get(f"{currency}_24h_vol"),
                        "market_cap": coin_data.get(f"{currency}_market_cap"),
                        "currency": currency.upper()
                    })

            await cache_set(cache_key, results, ttl=CACHE_TTL)
            return results
    except Exception as e:
        print(f"Error fetching multiple prices: {e}")
        return []

async def get_coin_details(coin_id: str) -> Optional[dict]:
    """Get detailed info for a coin."""
    cache_key = f"crypto:details:{coin_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE}/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false"
                },
                timeout=10.0
            )

            if response.status_code != 200:
                return None

            data = response.json()

            result = {
                "id": data["id"],
                "symbol": data["symbol"].upper(),
                "name": data["name"],
                "image": data.get("image", {}).get("small"),
                "current_price": data.get("market_data", {}).get("current_price", {}).get("usd"),
                "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd"),
                "market_cap_rank": data.get("market_cap_rank"),
                "total_volume": data.get("market_data", {}).get("total_volume", {}).get("usd"),
                "high_24h": data.get("market_data", {}).get("high_24h", {}).get("usd"),
                "low_24h": data.get("market_data", {}).get("low_24h", {}).get("usd"),
                "price_change_24h": data.get("market_data", {}).get("price_change_24h"),
                "price_change_percentage_24h": data.get("market_data", {}).get("price_change_percentage_24h"),
                "price_change_percentage_7d": data.get("market_data", {}).get("price_change_percentage_7d"),
                "circulating_supply": data.get("market_data", {}).get("circulating_supply"),
                "total_supply": data.get("market_data", {}).get("total_supply"),
                "ath": data.get("market_data", {}).get("ath", {}).get("usd"),
                "ath_change_percentage": data.get("market_data", {}).get("ath_change_percentage", {}).get("usd")
            }

            await cache_set(cache_key, result, ttl=CACHE_TTL)
            return result
    except Exception as e:
        print(f"Error fetching coin details: {e}")
        return None

async def get_coin_chart(coin_id: str, days: int = 7, currency: str = "usd") -> Optional[dict]:
    """Get price chart data for a coin."""
    cache_key = f"crypto:chart:{coin_id}:{days}:{currency}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
                params={
                    "vs_currency": currency,
                    "days": days
                },
                timeout=10.0
            )

            if response.status_code != 200:
                return None

            data = response.json()
            prices = data.get("prices", [])

            # Simplify data points
            result = {
                "id": coin_id,
                "days": days,
                "currency": currency.upper(),
                "prices": [{"timestamp": p[0], "price": p[1]} for p in prices]
            }

            # Shorter cache for shorter timeframes
            ttl = 60 if days <= 1 else CACHE_TTL
            await cache_set(cache_key, result, ttl=ttl)
            return result
    except Exception as e:
        print(f"Error fetching coin chart: {e}")
        return None
```

### 2. Crypto API Endpoints

#### app/api/v1/endpoints/crypto.py:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.crypto_service import (
    search_coins,
    get_coin_price,
    get_multiple_prices,
    get_coin_details,
    get_coin_chart
)

router = APIRouter(prefix="/crypto", tags=["Cryptocurrency"])

@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user)
):
    """Search for cryptocurrencies."""
    results = await search_coins(q)
    return {"results": results}

@router.get("/price/{coin_id}")
async def get_price(
    coin_id: str,
    currency: str = Query("usd", regex="^(usd|eur|gbp|btc)$"),
    current_user: User = Depends(get_current_user)
):
    """Get price for a cryptocurrency."""
    price = await get_coin_price(coin_id, currency)
    if not price:
        raise HTTPException(status_code=404, detail="Coin not found")
    return price

@router.post("/prices")
async def get_prices(
    coin_ids: List[str],
    currency: str = Query("usd", regex="^(usd|eur|gbp|btc)$"),
    current_user: User = Depends(get_current_user)
):
    """Get prices for multiple cryptocurrencies."""
    if len(coin_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 coins allowed")
    prices = await get_multiple_prices(coin_ids, currency)
    return {"prices": prices}

@router.get("/details/{coin_id}")
async def get_details(
    coin_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed info for a cryptocurrency."""
    details = await get_coin_details(coin_id)
    if not details:
        raise HTTPException(status_code=404, detail="Coin not found")
    return details

@router.get("/chart/{coin_id}")
async def get_chart(
    coin_id: str,
    days: int = Query(7, ge=1, le=365),
    currency: str = Query("usd", regex="^(usd|eur|gbp|btc)$"),
    current_user: User = Depends(get_current_user)
):
    """Get price chart data for a cryptocurrency."""
    chart = await get_coin_chart(coin_id, days, currency)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart data not found")
    return chart
```

#### Update app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, weather, widgets, stocks, crypto

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(weather.router)
api_router.include_router(widgets.router)
api_router.include_router(stocks.router)
api_router.include_router(crypto.router)
```

### 3. Frontend Crypto Widget

#### src/components/widgets/CryptoWidget.jsx:
```jsx
import { useState, useEffect } from 'react';
import api from '../../services/api';

const TIMEFRAMES = [
  { value: 1, label: '24H' },
  { value: 7, label: '7D' },
  { value: 30, label: '30D' },
  { value: 90, label: '90D' },
];

const DEFAULT_COINS = ['bitcoin', 'ethereum', 'solana'];

export default function CryptoWidget({ config }) {
  const [coins, setCoins] = useState([]);
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [details, setDetails] = useState(null);
  const [chart, setChart] = useState(null);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const coinIds = config.coins || DEFAULT_COINS;

  useEffect(() => {
    fetchPrices();
  }, [coinIds.join(',')]);

  useEffect(() => {
    if (selectedCoin) {
      fetchDetails(selectedCoin);
      fetchChart(selectedCoin, days);
    }
  }, [selectedCoin, days]);

  const fetchPrices = async () => {
    try {
      setLoading(true);
      const response = await api.post('/crypto/prices', coinIds);
      setCoins(response.data.prices);
      if (response.data.prices.length > 0 && !selectedCoin) {
        setSelectedCoin(response.data.prices[0].id);
      }
    } catch (err) {
      console.error('Failed to load crypto prices:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetails = async (coinId) => {
    try {
      const response = await api.get(`/crypto/details/${coinId}`);
      setDetails(response.data);
    } catch (err) {
      console.error('Failed to load coin details:', err);
    }
  };

  const fetchChart = async (coinId, days) => {
    try {
      const response = await api.get(`/crypto/chart/${coinId}`, {
        params: { days }
      });
      setChart(response.data);
    } catch (err) {
      console.error('Failed to load chart:', err);
    }
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      setSearching(true);
      const response = await api.get('/crypto/search', {
        params: { q: query }
      });
      setSearchResults(response.data.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleAddCoin = (coin) => {
    if (!coinIds.includes(coin.id)) {
      const newCoins = [...coinIds, coin.id];
      config.onConfigChange?.({ coins: newCoins });
    }
    setShowAdd(false);
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleRemoveCoin = (coinId) => {
    const newCoins = coinIds.filter(id => id !== coinId);
    config.onConfigChange?.({ coins: newCoins });
    if (selectedCoin === coinId) {
      setSelectedCoin(newCoins[0] || null);
    }
  };

  const formatPrice = (price) => {
    if (!price) return '-';
    if (price < 0.01) return `$${price.toFixed(6)}`;
    if (price < 1) return `$${price.toFixed(4)}`;
    return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatNumber = (num) => {
    if (!num) return '-';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (coins.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <span className="text-4xl mb-3">₿</span>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          Add cryptocurrencies to track
        </p>
        <button
          onClick={() => setShowAdd(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
        >
          Add Crypto
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Coin List */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-3">
        {coins.map((coin) => (
          <button
            key={coin.id}
            onClick={() => setSelectedCoin(coin.id)}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-left transition-colors ${
              selectedCoin === coin.id
                ? 'bg-orange-100 dark:bg-orange-900/30 border-orange-500'
                : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
            } border ${selectedCoin === coin.id ? 'border-orange-500' : 'border-transparent'}`}
          >
            <div className="font-medium text-xs text-gray-500 dark:text-gray-400 uppercase">
              {coin.id.slice(0, 3)}
            </div>
            <div className="text-sm font-semibold text-gray-900 dark:text-white">
              {formatPrice(coin.price)}
            </div>
            <div className={`text-xs ${coin.change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h?.toFixed(2)}%
            </div>
          </button>
        ))}
        <button
          onClick={() => setShowAdd(true)}
          className="flex-shrink-0 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 border border-dashed border-gray-300 dark:border-gray-600 text-gray-500"
        >
          <span className="text-xl">+</span>
        </button>
      </div>

      {/* Selected Coin Details */}
      {details && (
        <>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {details.image && (
                <img src={details.image} alt={details.name} className="w-6 h-6" />
              )}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {details.name}
                </h3>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {details.symbol} • Rank #{details.market_cap_rank}
                </span>
              </div>
            </div>
            <button
              onClick={() => handleRemoveCoin(details.id)}
              className="text-xs text-red-500 hover:text-red-600"
            >
              Remove
            </button>
          </div>

          {/* Mini Chart */}
          <div className="flex-1 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-2 mb-2 min-h-[80px]">
            {chart && chart.prices.length > 0 ? (
              <MiniChart 
                data={chart.prices} 
                positive={details.price_change_percentage_24h >= 0} 
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                Loading chart...
              </div>
            )}
          </div>

          {/* Timeframe Selector */}
          <div className="flex gap-1 mb-2">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setDays(tf.value)}
                className={`px-2 py-1 text-xs rounded ${
                  days === tf.value
                    ? 'bg-orange-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">24h High</span>
              <span className="text-gray-900 dark:text-white">{formatPrice(details.high_24h)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">24h Low</span>
              <span className="text-gray-900 dark:text-white">{formatPrice(details.low_24h)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Market Cap</span>
              <span className="text-gray-900 dark:text-white">{formatNumber(details.market_cap)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Volume</span>
              <span className="text-gray-900 dark:text-white">{formatNumber(details.total_volume)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">ATH</span>
              <span className="text-gray-900 dark:text-white">{formatPrice(details.ath)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">From ATH</span>
              <span className="text-red-500">{details.ath_change_percentage?.toFixed(1)}%</span>
            </div>
          </div>
        </>
      )}

      {/* Add Coin Modal */}
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowAdd(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg p-4 w-80 max-h-96 overflow-hidden flex flex-col">
            <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Add Cryptocurrency</h3>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search (e.g., Bitcoin, ETH)"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm mb-3"
              autoFocus
            />

            <div className="flex-1 overflow-y-auto">
              {searching ? (
                <div className="text-center py-4 text-gray-500">Searching...</div>
              ) : searchResults.length > 0 ? (
                <div className="space-y-1">
                  {searchResults.map((coin) => (
                    <button
                      key={coin.id}
                      onClick={() => handleAddCoin(coin)}
                      className="w-full flex items-center gap-2 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-left"
                    >
                      {coin.thumb && (
                        <img src={coin.thumb} alt={coin.name} className="w-6 h-6" />
                      )}
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {coin.name}
                        </div>
                        <div className="text-xs text-gray-500">{coin.symbol}</div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : searchQuery.length >= 2 ? (
                <div className="text-center py-4 text-gray-500">No results found</div>
              ) : (
                <div className="text-center py-4 text-gray-500 text-sm">
                  Type to search for cryptocurrencies
                </div>
              )}
            </div>

            <button
              onClick={() => setShowAdd(false)}
              className="mt-3 w-full px-3 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Simple SVG line chart component
function MiniChart({ data, positive }) {
  if (!data || data.length === 0) return null;

  const prices = data.map(d => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  const width = 100;
  const height = 60;
  const padding = 2;

  const points = prices.map((price, i) => {
    const x = padding + (i / (prices.length - 1)) * (width - padding * 2);
    const y = height - padding - ((price - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  const color = positive ? '#22c55e' : '#ef4444';

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <polyline
        points={points}
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

### 4. Update Widget Registry

#### Update src/components/widgets/widgetRegistry.js:
```javascript
const widgetRegistry = {
  weather: {
    component: () => import('./WeatherWidget'),
    name: 'Weather',
    description: 'Current weather and forecast',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 4 }
  },
  stocks: {
    component: () => import('./StockWidget'),
    name: 'Stocks',
    description: 'Track stock prices and charts',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 2 },
    maxSize: { w: 6, h: 5 }
  },
  crypto: {
    component: () => import('./CryptoWidget'),
    name: 'Cryptocurrency',
    description: 'Track crypto prices and market data',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 2 },
    maxSize: { w: 6, h: 5 }
  },
  placeholder: {
    component: () => import('./PlaceholderWidget'),
    name: 'Placeholder',
    description: 'Placeholder widget',
    defaultSize: { w: 2, h: 2 },
    minSize: { w: 1, h: 1 },
    maxSize: { w: 4, h: 4 }
  }
};

export function getWidget(type) {
  return widgetRegistry[type] || widgetRegistry.placeholder;
}

export function getAvailableWidgets() {
  return Object.entries(widgetRegistry)
    .filter(([type]) => type !== 'placeholder')
    .map(([type, config]) => ({
      type,
      name: config.name,
      description: config.description,
      defaultSize: config.defaultSize
    }));
}

export default widgetRegistry;
```

## Unit Tests

### tests/test_crypto.py:
```python
import pytest
from app.services.crypto_service import (
    search_coins,
    get_coin_price,
    get_coin_details,
    get_coin_chart
)

@pytest.mark.asyncio
async def test_search_coins():
    results = await search_coins("bitcoin")
    assert len(results) > 0
    assert any(r["id"] == "bitcoin" for r in results)

@pytest.mark.asyncio
async def test_get_coin_price():
    price = await get_coin_price("bitcoin")
    assert price is not None
    assert price["id"] == "bitcoin"
    assert "price" in price
    assert price["price"] > 0

@pytest.mark.asyncio
async def test_get_coin_price_invalid():
    price = await get_coin_price("invalidcoin123xyz")
    assert price is None

@pytest.mark.asyncio
async def test_get_coin_details():
    details = await get_coin_details("ethereum")
    assert details is not None
    assert details["symbol"] == "ETH"
    assert "market_cap" in details
    assert "current_price" in details

@pytest.mark.asyncio
async def test_get_coin_chart():
    chart = await get_coin_chart("bitcoin", days=7)
    assert chart is not None
    assert "prices" in chart
    assert len(chart["prices"]) > 0
```

## Acceptance Criteria
- [ ] Crypto widget displays in widget list
- [ ] Can search and add cryptocurrencies
- [ ] Prices display with 24h change
- [ ] Mini chart shows price history
- [ ] Timeframe selector works (24H, 7D, 30D, 90D)
- [ ] Detailed stats display (market cap, volume, ATH)
- [ ] Can remove coins from watchlist
- [ ] Coin images/icons display
- [ ] Data caches appropriately (2 min)
- [ ] Unit tests pass

## Estimated Time
3-4 hours

## Next Task
Task 009: Server Monitoring Dashboard Integration
