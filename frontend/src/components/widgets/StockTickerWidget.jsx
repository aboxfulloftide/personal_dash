import { useState, useEffect } from 'react';
import api from '../../services/api';

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

function StockRow({ symbol, shares, price, changePercent, onRemove }) {
  const total = price !== null ? price * shares : null;
  const isPositive = changePercent !== null && changePercent >= 0;

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
        <span className="text-gray-500 dark:text-gray-400 w-8 text-right">
          {shares}×
        </span>
        <span className="font-medium text-gray-800 dark:text-gray-200 w-20 text-right">
          {formatCurrency(total)}
        </span>
      </div>
    </div>
  );
}

function AddHoldingModal({ isOpen, onClose, onAdd }) {
  const [symbol, setSymbol] = useState('');
  const [shares, setShares] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!symbol.trim() || !shares) return;
    onAdd({ symbol: symbol.trim().toUpperCase(), shares: parseFloat(shares) });
    setSymbol('');
    setShares('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-xs w-full mx-4 p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Add Stock</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
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

export default function StockTickerWidget({ config, onConfigChange }) {
  const [quotes, setQuotes] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const holdings = config.holdings || [];

  const fetchQuotes = async () => {
    if (holdings.length === 0) return;

    const symbols = holdings.map((h) => h.symbol).join(',');
    setLoading(true);
    setError(null);

    try {
      const params = {
        symbols,
        provider: config.api_provider || 'alphavantage',
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
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch quotes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotes();
    const interval = setInterval(fetchQuotes, (config.refresh_interval || 300) * 1000);
    return () => clearInterval(interval);
  }, [holdings.length, config.api_provider, config.api_key, config.refresh_interval]);

  const handleAddHolding = (holding) => {
    const newHoldings = [...holdings, holding];
    onConfigChange?.({ ...config, holdings: newHoldings });
  };

  const handleRemoveHolding = (index) => {
    const newHoldings = holdings.filter((_, i) => i !== index);
    onConfigChange?.({ ...config, holdings: newHoldings });
  };

  const totalValue = holdings.reduce((sum, h) => {
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
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {loading ? 'Updating...' : error ? 'Error' : `${holdings.length} stocks`}
        </span>
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
              onRemove={() => handleRemoveHolding(index)}
            />
          );
        })}
      </div>

      <div className="pt-2 mt-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500 dark:text-gray-400">Total Value</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">
            {formatCurrency(totalValue)}
          </span>
        </div>
      </div>

      <AddHoldingModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddHolding}
      />
    </div>
  );
}
