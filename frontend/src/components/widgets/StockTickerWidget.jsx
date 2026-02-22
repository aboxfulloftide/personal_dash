import { useState, useEffect, useMemo } from 'react';
import { Briefcase, Eye, TrendingUp } from 'lucide-react';
import api from '../../services/api';
import PortfolioGraph from './PortfolioGraph';

// Minimum refresh intervals per provider (in seconds) to avoid rate limits
// With database caching, we can use 20-minute intervals to reduce API calls
const MIN_REFRESH_INTERVALS = {
  yahoo: 1200,        // 20 minutes (database fallback prevents blank widgets)
  alphavantage: 1200, // 20 minutes (3 attempts per hour, ~72 requests/day per symbol)
  finnhub: 1200,      // 20 minutes (60 calls/min limit, plenty of headroom)
};

function formatCurrency(value) {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value) {
  if (value === null || value === undefined) return '';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function StockRow({ symbol, shares, price, changePercent, type, onRemove }) {
  const total = price !== null ? price * shares : null;
  const isPositive = changePercent !== null && changePercent >= 0;
  const isPortfolio = type === 'portfolio';

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-100 dark:border-gray-700 last:border-0">
      <div className="flex items-center gap-2 min-w-0">
        <button
          onClick={onRemove}
          className="text-gray-400 hover:text-red-500 text-xs"
          title="Remove"
        >
          ×
        </button>
        <span title={isPortfolio ? 'Portfolio' : 'Watchlist'}>
          {isPortfolio ? (
            <Briefcase className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          ) : (
            <Eye className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
          )}
        </span>
        <span className="font-medium text-gray-800 dark:text-gray-200 text-sm">
          {symbol}
        </span>
      </div>
      <div className="flex items-center gap-3 text-xs">
        <span className="text-gray-600 dark:text-gray-400">
          {formatCurrency(price)}
        </span>
        <span className={`w-14 text-right ${isPositive ? 'text-green-600' : 'text-red-500'}`}>
          {formatPercent(changePercent)}
        </span>
        {isPortfolio ? (
          <>
            <span className="text-gray-500 dark:text-gray-400 w-8 text-right">
              {shares}×
            </span>
            <span className="font-medium text-gray-800 dark:text-gray-200 w-20 text-right">
              {formatCurrency(total)}
            </span>
          </>
        ) : (
          <span className="text-gray-400 dark:text-gray-500 text-xs italic w-28 text-right">
            watching
          </span>
        )}
      </div>
    </div>
  );
}

function AddHoldingModal({ isOpen, onClose, onAdd }) {
  const [symbol, setSymbol] = useState('');
  const [shares, setShares] = useState('');
  const [type, setType] = useState('portfolio');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!symbol.trim()) return;
    if (type === 'portfolio' && !shares) return;

    onAdd({
      symbol: symbol.trim().toUpperCase(),
      shares: type === 'portfolio' ? parseFloat(shares) : 0,
      type: type
    });
    setSymbol('');
    setShares('');
    setType('portfolio');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-xs w-full mx-4 p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Add Stock</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Type</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setType('portfolio')}
                className={`flex-1 px-3 py-2 rounded text-sm transition-colors flex items-center justify-center gap-1.5 ${
                  type === 'portfolio'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                <Briefcase className="w-4 h-4" />
                <span>Portfolio</span>
              </button>
              <button
                type="button"
                onClick={() => setType('watchlist')}
                className={`flex-1 px-3 py-2 rounded text-sm transition-colors flex items-center justify-center gap-1.5 ${
                  type === 'watchlist'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                <Eye className="w-4 h-4" />
                <span>Watchlist</span>
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="AAPL"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              required
            />
          </div>
          {type === 'portfolio' && (
            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Shares</label>
              <input
                type="number"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                placeholder="10"
                step="any"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                required
              />
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-3 py-1.5 text-gray-600 dark:text-gray-400 text-sm">
              Cancel
            </button>
            <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Add
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function formatTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function StockTickerWidget({ config, onConfigChange }) {
  const [quotes, setQuotes] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [showGraph, setShowGraph] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState(null);

  const holdings = config.holdings || [];

  // One-time migration: Add type field to existing holdings
  useEffect(() => {
    const needsMigration = holdings.some(h => !h.type);
    if (needsMigration) {
      const migratedHoldings = holdings.map(h => ({
        ...h,
        type: h.type || 'portfolio'
      }));
      onConfigChange?.({ ...config, holdings: migratedHoldings });
    }
  }, []); // Run once on mount

  const fetchQuotes = async () => {
    if (holdings.length === 0) return;

    const symbols = holdings.map((h) => h.symbol).join(',');
    setLoading(true);
    setError(null);

    try {
      const params = {
        symbols,
        provider: config.api_provider || 'yahoo',
      };
      if (config.api_key) {
        params.api_key = config.api_key;
      }

      const resp = await api.get('/finance/stocks', { params });
      const quoteMap = {};
      for (const q of resp.data.quotes) {
        quoteMap[q.symbol] = q;
      }
      setQuotes(quoteMap);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch quotes');
    } finally {
      setLoading(false);
    }
  };

  // Calculate effective refresh interval based on provider limits
  const effectiveRefreshInterval = useMemo(() => {
    const provider = config.api_provider || 'yahoo';
    const minInterval = MIN_REFRESH_INTERVALS[provider] || 60;
    const userInterval = config.refresh_interval || 300;
    return Math.max(userInterval, minInterval);
  }, [config.api_provider, config.refresh_interval]);

  useEffect(() => {
    fetchQuotes();
    const interval = setInterval(fetchQuotes, effectiveRefreshInterval * 1000);
    return () => clearInterval(interval);
  }, [holdings.length, config.api_provider, config.api_key, effectiveRefreshInterval]);

  const handleAddHolding = (holding) => {
    const newHoldings = [...holdings, holding];
    onConfigChange?.({ ...config, holdings: newHoldings });
  };

  const handleRemoveHolding = (index) => {
    const newHoldings = holdings.filter((_, i) => i !== index);
    onConfigChange?.({ ...config, holdings: newHoldings });
  };

  const fetchPortfolioHistory = async () => {
    const portfolioHoldings = holdings.filter(h => (h.type || 'portfolio') === 'portfolio');
    if (portfolioHoldings.length === 0) return;

    setGraphLoading(true);
    setGraphError(null);

    try {
      const params = {
        holdings: JSON.stringify(portfolioHoldings),
        days: 90,
      };
      const resp = await api.get('/finance/stocks/portfolio-history', { params });
      setGraphData(resp.data);
    } catch (err) {
      setGraphError(err.response?.data?.detail || 'Failed to load portfolio history');
    } finally {
      setGraphLoading(false);
    }
  };

  // Lazy load graph data when expanded
  useEffect(() => {
    if (showGraph && !graphData) {
      fetchPortfolioHistory();
    }
  }, [showGraph]);

  const portfolioHoldings = holdings.filter(h => (h.type || 'portfolio') === 'portfolio');
  const watchlistHoldings = holdings.filter(h => h.type === 'watchlist');

  const totalValue = portfolioHoldings.reduce((sum, h) => {
    const quote = quotes[h.symbol];
    if (quote?.price) {
      return sum + quote.price * h.shares;
    }
    return sum;
  }, 0);

  if (holdings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <p className="text-sm">No stocks tracked</p>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-xs text-blue-500 hover:underline mt-1"
        >
          Add your first stock
        </button>
        <AddHoldingModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddHolding}
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            {loading ? 'Updating...' : error ? 'Error' : (
              <>
                {portfolioHoldings.length > 0 && (
                  <span className="flex items-center gap-0.5">
                    <Briefcase className="w-3 h-3" />
                    {portfolioHoldings.length}
                  </span>
                )}
                {portfolioHoldings.length > 0 && watchlistHoldings.length > 0 && <span>•</span>}
                {watchlistHoldings.length > 0 && (
                  <span className="flex items-center gap-0.5">
                    <Eye className="w-3 h-3" />
                    {watchlistHoldings.length}
                  </span>
                )}
              </>
            )}
          </span>
          {lastUpdated && !loading && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {formatTimeAgo(lastUpdated)}
            </span>
          )}
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
        >
          + Add
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500 mb-2">{error}</p>
      )}

      <div className="flex-1 overflow-auto">
        {holdings.map((holding, index) => {
          const quote = quotes[holding.symbol] || {};
          return (
            <StockRow
              key={`${holding.symbol}-${index}`}
              symbol={holding.symbol}
              shares={holding.shares}
              price={quote.price}
              changePercent={quote.change_percent}
              type={holding.type || 'portfolio'}
              onRemove={() => handleRemoveHolding(index)}
            />
          );
        })}
      </div>

      {/* Portfolio Graph Section */}
      {portfolioHoldings.length > 0 && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {!showGraph ? (
            <button
              onClick={() => setShowGraph(true)}
              className="w-full px-2 py-2 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
            >
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5" />
                Show Portfolio Graph
              </span>
              <span>▼</span>
            </button>
          ) : (
            <div className="px-2 py-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Portfolio History (90 days)</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={fetchPortfolioHistory}
                    className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                    disabled={graphLoading}
                  >
                    {graphLoading ? '...' : '↻ Refresh'}
                  </button>
                  <button
                    onClick={() => setShowGraph(false)}
                    className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    ▲ Hide
                  </button>
                </div>
              </div>

              {graphLoading && !graphData && (
                <div className="flex items-center justify-center h-48 bg-gray-100 dark:bg-gray-700 rounded">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                </div>
              )}

              {graphError && (
                <div className="flex flex-col items-center justify-center h-48 bg-gray-100 dark:bg-gray-700 rounded text-xs text-red-500">
                  <p className="mb-2">{graphError}</p>
                  <button
                    onClick={fetchPortfolioHistory}
                    className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Retry
                  </button>
                </div>
              )}

              {!graphLoading && !graphError && graphData && (
                <PortfolioGraph data={graphData} currency="USD" />
              )}
            </div>
          )}
        </div>
      )}

      {portfolioHoldings.length > 0 && (
        <div className="pt-2 mt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
              <Briefcase className="w-3 h-3" />
              Portfolio Value
            </span>
            <span className="font-semibold text-gray-800 dark:text-gray-200">
              {formatCurrency(totalValue)}
            </span>
          </div>
        </div>
      )}

      <AddHoldingModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddHolding}
      />
    </div>
  );
}
