import { useState, useEffect, useMemo } from 'react';
import { Briefcase, Eye, TrendingUp } from 'lucide-react';
import api from '../../services/api';
import PortfolioGraph from './PortfolioGraph';

// Minimum refresh intervals per provider (in seconds) to avoid rate limits
// With database caching, we can use 20-minute intervals to reduce API calls
const MIN_REFRESH_INTERVALS = {
  coingecko: 1200,  // 20 minutes (database fallback prevents blank widgets)
  coincap: 1200,    // 20 minutes (very generous limit, but consistent with stocks)
};

const CURRENCY_SYMBOLS = {
  usd: '$',
  eur: '€',
  gbp: '£',
};

function formatCurrency(value, currency = 'usd') {
  if (value === null || value === undefined) return '—';
  const symbol = CURRENCY_SYMBOLS[currency] || '$';
  return `${symbol}${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
  if (value === null || value === undefined) return '';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function formatTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

function CryptoRow({ id, symbol, amount, price, change24h, currency, type, onRemove }) {
  const total = price !== null ? price * amount : null;
  const isPositive = change24h !== null && change24h >= 0;
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
          {formatCurrency(price, currency)}
        </span>
        <span className={`w-14 text-right ${isPositive ? 'text-green-600' : 'text-red-500'}`}>
          {formatPercent(change24h)}
        </span>
        {isPortfolio ? (
          <>
            <span className="text-gray-500 dark:text-gray-400 w-12 text-right">
              {amount}×
            </span>
            <span className="font-medium text-gray-800 dark:text-gray-200 w-20 text-right">
              {formatCurrency(total, currency)}
            </span>
          </>
        ) : (
          <span className="text-gray-400 dark:text-gray-500 text-xs italic w-32 text-right">
            watching
          </span>
        )}
      </div>
    </div>
  );
}

function AddHoldingModal({ isOpen, onClose, onAdd }) {
  const [coin, setCoin] = useState('bitcoin');
  const [amount, setAmount] = useState('');
  const [type, setType] = useState('portfolio');

  const commonCoins = [
    { value: 'bitcoin', label: 'Bitcoin (BTC)' },
    { value: 'ethereum', label: 'Ethereum (ETH)' },
    { value: 'solana', label: 'Solana (SOL)' },
    { value: 'cardano', label: 'Cardano (ADA)' },
    { value: 'dogecoin', label: 'Dogecoin (DOGE)' },
    { value: 'ripple', label: 'Ripple (XRP)' },
    { value: 'polkadot', label: 'Polkadot (DOT)' },
    { value: 'litecoin', label: 'Litecoin (LTC)' },
  ];

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!coin) return;
    if (type === 'portfolio' && !amount) return;

    onAdd({
      coin,
      amount: type === 'portfolio' ? parseFloat(amount) : 0,
      type: type
    });
    setCoin('bitcoin');
    setAmount('');
    setType('portfolio');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-xs w-full mx-4 p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Add Crypto</h3>
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
            <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Coin</label>
            <select
              value={coin}
              onChange={(e) => setCoin(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              {commonCoins.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          {type === 'portfolio' && (
            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Amount</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.4931"
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

export default function CryptoWidget({ config, onConfigChange }) {
  const [prices, setPrices] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [showGraph, setShowGraph] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState(null);

  const holdings = config.holdings || [];
  const currency = config.currency || 'usd';

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

  const fetchPrices = async () => {
    if (holdings.length === 0) return;

    const coins = holdings.map((h) => h.coin).join(',');
    setLoading(true);
    setError(null);

    try {
      const params = {
        coins,
        currency,
        provider: config.api_provider || 'coingecko',
      };
      if (config.api_key) {
        params.api_key = config.api_key;
      }

      const resp = await api.get('/finance/crypto', { params });
      const priceMap = {};
      for (const p of resp.data.prices) {
        priceMap[p.id] = p;
      }
      setPrices(priceMap);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch prices');
    } finally {
      setLoading(false);
    }
  };

  // Calculate effective refresh interval based on provider limits
  const effectiveRefreshInterval = useMemo(() => {
    const provider = config.api_provider || 'coingecko';
    const minInterval = MIN_REFRESH_INTERVALS[provider] || 60;
    const userInterval = config.refresh_interval || 300;
    return Math.max(userInterval, minInterval);
  }, [config.api_provider, config.refresh_interval]);

  useEffect(() => {
    fetchPrices();
    const interval = setInterval(fetchPrices, effectiveRefreshInterval * 1000);
    return () => clearInterval(interval);
  }, [holdings.length, config.api_provider, config.api_key, effectiveRefreshInterval, currency]);

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
      const resp = await api.get('/finance/crypto/portfolio-history', { params });
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
    const priceData = prices[h.coin];
    if (priceData?.price) {
      return sum + priceData.price * h.amount;
    }
    return sum;
  }, 0);

  if (holdings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-sm">No crypto tracked</p>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-xs text-blue-500 hover:underline mt-1"
        >
          Add your first coin
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
          const priceData = prices[holding.coin] || {};
          return (
            <CryptoRow
              key={`${holding.coin}-${index}`}
              id={holding.coin}
              symbol={priceData.symbol || holding.coin.toUpperCase().slice(0, 4)}
              amount={holding.amount}
              price={priceData.price}
              change24h={priceData.change_24h}
              currency={currency}
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
                <PortfolioGraph data={graphData} currency={currency.toUpperCase()} />
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
              {formatCurrency(totalValue, currency)}
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
