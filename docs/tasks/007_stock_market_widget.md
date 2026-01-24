# Task 007: Stock Market Widget

## Objective
Build the Stock Market widget using Yahoo Finance (yfinance) to display stock prices, changes, and basic charts.

## Prerequisites
- Task 006 completed
- Widget framework working

## Dependencies to Install

### Backend:
```bash
cd backend
pip install yfinance
```

## API Information
- **Library**: yfinance (unofficial Yahoo Finance API wrapper)
- **Cost**: Free
- **Rate Limit**: Be respectful, cache aggressively
- **Note**: Not for commercial use, data may be delayed

## Deliverables

### 1. Backend Stock Service

#### app/services/stock_service.py:
```python
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, List
from app.core.cache import cache_get, cache_set

CACHE_TTL = 300  # 5 minutes for stock data

async def get_stock_quote(symbol: str) -> Optional[dict]:
    """Get current stock quote."""
    cache_key = f"stock:quote:{symbol.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or 'regularMarketPrice' not in info:
            # Try fast_info as fallback
            fast = ticker.fast_info
            if not fast:
                return None

            result = {
                "symbol": symbol.upper(),
                "name": symbol.upper(),
                "price": fast.get('lastPrice'),
                "change": fast.get('lastPrice', 0) - fast.get('previousClose', 0),
                "change_percent": ((fast.get('lastPrice', 0) - fast.get('previousClose', 0)) / fast.get('previousClose', 1)) * 100 if fast.get('previousClose') else 0,
                "previous_close": fast.get('previousClose'),
                "open": fast.get('open'),
                "day_high": fast.get('dayHigh'),
                "day_low": fast.get('dayLow'),
                "volume": fast.get('lastVolume'),
                "market_cap": fast.get('marketCap'),
                "currency": "USD"
            }
        else:
            price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            prev_close = info.get('regularMarketPreviousClose', info.get('previousClose', 0))
            change = price - prev_close if price and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            result = {
                "symbol": symbol.upper(),
                "name": info.get('shortName', info.get('longName', symbol.upper())),
                "price": price,
                "change": change,
                "change_percent": change_pct,
                "previous_close": prev_close,
                "open": info.get('regularMarketOpen', info.get('open')),
                "day_high": info.get('regularMarketDayHigh', info.get('dayHigh')),
                "day_low": info.get('regularMarketDayLow', info.get('dayLow')),
                "volume": info.get('regularMarketVolume', info.get('volume')),
                "market_cap": info.get('marketCap'),
                "currency": info.get('currency', 'USD'),
                "exchange": info.get('exchange'),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow')
            }

        await cache_set(cache_key, result, ttl=CACHE_TTL)
        return result

    except Exception as e:
        print(f"Error fetching stock {symbol}: {e}")
        return None

async def get_stock_history(symbol: str, period: str = "1mo") -> Optional[dict]:
    """Get stock price history for charting."""
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        period = "1mo"

    cache_key = f"stock:history:{symbol.upper()}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        ticker = yf.Ticker(symbol)

        # Determine interval based on period
        interval_map = {
            "1d": "5m",
            "5d": "15m",
            "1mo": "1d",
            "3mo": "1d",
            "6mo": "1d",
            "1y": "1wk",
            "2y": "1wk",
            "5y": "1mo"
        }
        interval = interval_map.get(period, "1d")

        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            return None

        # Convert to list of data points
        data_points = []
        for date, row in hist.iterrows():
            data_points.append({
                "date": date.strftime("%Y-%m-%d %H:%M") if interval in ["5m", "15m"] else date.strftime("%Y-%m-%d"),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })

        result = {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "data": data_points
        }

        # Cache based on period (shorter periods = shorter cache)
        ttl = 60 if period in ["1d", "5d"] else CACHE_TTL
        await cache_set(cache_key, result, ttl=ttl)
        return result

    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return None

async def search_stocks(query: str) -> List[dict]:
    """Search for stocks by name or symbol."""
    cache_key = f"stock:search:{query.lower()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        # yfinance doesn't have great search, so we'll try the symbol directly
        ticker = yf.Ticker(query)
        info = ticker.info

        if info and info.get('symbol'):
            results = [{
                "symbol": info.get('symbol'),
                "name": info.get('shortName', info.get('longName', query)),
                "exchange": info.get('exchange'),
                "type": info.get('quoteType', 'EQUITY')
            }]
            await cache_set(cache_key, results, ttl=3600)
            return results

        return []

    except Exception as e:
        print(f"Error searching stocks: {e}")
        return []

async def get_multiple_quotes(symbols: List[str]) -> List[dict]:
    """Get quotes for multiple symbols."""
    results = []
    for symbol in symbols[:10]:  # Limit to 10 symbols
        quote = await get_stock_quote(symbol)
        if quote:
            results.append(quote)
    return results
```

### 2. Stock API Endpoints

#### app/api/v1/endpoints/stocks.py:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.stock_service import (
    get_stock_quote,
    get_stock_history,
    search_stocks,
    get_multiple_quotes
)

router = APIRouter(prefix="/stocks", tags=["Stocks"])

@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get stock quote for a symbol."""
    quote = await get_stock_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Stock not found")
    return quote

@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y)$"),
    current_user: User = Depends(get_current_user)
):
    """Get stock price history."""
    history = await get_stock_history(symbol, period)
    if not history:
        raise HTTPException(status_code=404, detail="Stock history not found")
    return history

@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user)
):
    """Search for stocks."""
    results = await search_stocks(q)
    return {"results": results}

@router.post("/quotes")
async def get_quotes(
    symbols: List[str],
    current_user: User = Depends(get_current_user)
):
    """Get quotes for multiple symbols."""
    if len(symbols) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 symbols allowed")
    quotes = await get_multiple_quotes(symbols)
    return {"quotes": quotes}
```

#### Update app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, weather, widgets, stocks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(weather.router)
api_router.include_router(widgets.router)
api_router.include_router(stocks.router)
```

### 3. Frontend Stock Widget

#### src/components/widgets/StockWidget.jsx:
```jsx
import { useState, useEffect } from 'react';
import api from '../../services/api';

const PERIODS = [
  { value: '1d', label: '1D' },
  { value: '5d', label: '5D' },
  { value: '1mo', label: '1M' },
  { value: '3mo', label: '3M' },
  { value: '1y', label: '1Y' },
];

export default function StockWidget({ config }) {
  const [quotes, setQuotes] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [history, setHistory] = useState(null);
  const [period, setPeriod] = useState('1mo');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const symbols = config.symbols || ['AAPL', 'GOOGL', 'MSFT'];

  useEffect(() => {
    if (symbols.length > 0) {
      fetchQuotes();
    } else {
      setLoading(false);
    }
  }, [symbols.join(',')]);

  useEffect(() => {
    if (selectedStock) {
      fetchHistory(selectedStock);
    }
  }, [selectedStock, period]);

  const fetchQuotes = async () => {
    try {
      setLoading(true);
      const response = await api.post('/stocks/quotes', symbols);
      setQuotes(response.data.quotes);
      if (response.data.quotes.length > 0 && !selectedStock) {
        setSelectedStock(response.data.quotes[0].symbol);
      }
    } catch (err) {
      setError('Failed to load stocks');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (symbol) => {
    try {
      const response = await api.get(`/stocks/history/${symbol}`, {
        params: { period }
      });
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    const symbol = searchQuery.toUpperCase().trim();
    if (!symbols.includes(symbol)) {
      const newSymbols = [...symbols, symbol];
      config.onConfigChange?.({ symbols: newSymbols });
    }
    setSearchQuery('');
    setShowAdd(false);
  };

  const handleRemoveStock = (symbol) => {
    const newSymbols = symbols.filter(s => s !== symbol);
    config.onConfigChange?.({ symbols: newSymbols });
    if (selectedStock === symbol) {
      setSelectedStock(newSymbols[0] || null);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    return num?.toLocaleString() || '-';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (quotes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <span className="text-4xl mb-3">📈</span>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          Add stocks to track
        </p>
        <form onSubmit={handleAddStock} className="w-full max-w-xs">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter symbol (e.g., AAPL)"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm mb-2"
          />
          <button
            type="submit"
            className="w-full px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
          >
            Add Stock
          </button>
        </form>
      </div>
    );
  }

  const selectedQuote = quotes.find(q => q.symbol === selectedStock);

  return (
    <div className="h-full flex flex-col">
      {/* Stock List */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-3">
        {quotes.map((quote) => (
          <button
            key={quote.symbol}
            onClick={() => setSelectedStock(quote.symbol)}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-left transition-colors ${
              selectedStock === quote.symbol
                ? 'bg-blue-100 dark:bg-blue-900/50 border-blue-500'
                : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
            } border ${selectedStock === quote.symbol ? 'border-blue-500' : 'border-transparent'}`}
          >
            <div className="font-medium text-sm text-gray-900 dark:text-white">
              {quote.symbol}
            </div>
            <div className="text-sm font-semibold text-gray-900 dark:text-white">
              ${quote.price?.toFixed(2)}
            </div>
            <div className={`text-xs ${quote.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {quote.change >= 0 ? '+' : ''}{quote.change?.toFixed(2)} ({quote.change_percent?.toFixed(2)}%)
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

      {/* Selected Stock Details */}
      {selectedQuote && (
        <>
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {selectedQuote.name}
              </h3>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {selectedQuote.exchange} • {selectedQuote.currency}
              </div>
            </div>
            <button
              onClick={() => handleRemoveStock(selectedQuote.symbol)}
              className="text-xs text-red-500 hover:text-red-600"
            >
              Remove
            </button>
          </div>

          {/* Mini Chart Placeholder */}
          <div className="flex-1 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-2 mb-2 min-h-[80px]">
            {history && history.data.length > 0 ? (
              <MiniChart data={history.data} positive={selectedQuote.change >= 0} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                Loading chart...
              </div>
            )}
          </div>

          {/* Period Selector */}
          <div className="flex gap-1 mb-2">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-2 py-1 text-xs rounded ${
                  period === p.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Open</span>
              <span className="text-gray-900 dark:text-white">${selectedQuote.open?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Prev Close</span>
              <span className="text-gray-900 dark:text-white">${selectedQuote.previous_close?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Day High</span>
              <span className="text-gray-900 dark:text-white">${selectedQuote.day_high?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Day Low</span>
              <span className="text-gray-900 dark:text-white">${selectedQuote.day_low?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Volume</span>
              <span className="text-gray-900 dark:text-white">{formatNumber(selectedQuote.volume)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Mkt Cap</span>
              <span className="text-gray-900 dark:text-white">{formatNumber(selectedQuote.market_cap)}</span>
            </div>
          </div>
        </>
      )}

      {/* Add Stock Modal */}
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowAdd(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg p-4 w-80">
            <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Add Stock</h3>
            <form onSubmit={handleAddStock}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter symbol (e.g., TSLA)"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm mb-3"
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowAdd(false)}
                  className="flex-1 px-3 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
                >
                  Add
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Simple SVG line chart component
function MiniChart({ data, positive }) {
  if (!data || data.length === 0) return null;

  const prices = data.map(d => d.close);
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

### tests/test_stocks.py:
```python
import pytest
from app.services.stock_service import get_stock_quote, get_stock_history

@pytest.mark.asyncio
async def test_get_stock_quote():
    # Test with a known stock
    quote = await get_stock_quote("AAPL")
    assert quote is not None
    assert quote["symbol"] == "AAPL"
    assert "price" in quote
    assert "change" in quote
    assert "change_percent" in quote

@pytest.mark.asyncio
async def test_get_stock_quote_invalid():
    quote = await get_stock_quote("INVALIDXYZ123")
    assert quote is None

@pytest.mark.asyncio
async def test_get_stock_history():
    history = await get_stock_history("AAPL", "1mo")
    assert history is not None
    assert history["symbol"] == "AAPL"
    assert "data" in history
    assert len(history["data"]) > 0
    assert "close" in history["data"][0]

@pytest.mark.asyncio
async def test_get_stock_history_periods():
    for period in ["1d", "5d", "1mo", "3mo"]:
        history = await get_stock_history("MSFT", period)
        assert history is not None
        assert history["period"] == period
```

## Acceptance Criteria
- [ ] Stock widget displays in widget list
- [ ] Can add stocks by symbol
- [ ] Stock quotes display with price and change
- [ ] Mini chart shows price history
- [ ] Period selector changes chart timeframe
- [ ] Can remove stocks from watchlist
- [ ] Multiple stocks can be tracked
- [ ] Data caches appropriately
- [ ] Error handling for invalid symbols
- [ ] Unit tests pass

## Estimated Time
3-4 hours

## Next Task
Task 008: Cryptocurrency Widget
