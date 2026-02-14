import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

/**
 * Reusable portfolio graph component for stocks and crypto
 */
function PortfolioGraph({ data, currency = 'USD' }) {
  if (!data || !data.data_points || data.data_points.length === 0) {
    return (
      <div className="p-4 text-center text-gray-400">
        No historical data available. Data collection begins when you add holdings.
      </div>
    );
  }

  const {
    data_points,
    current_value,
    starting_value,
    total_gain_loss_pct,
    display_mode,
  } = data;

  // Determine color based on gain/loss
  const isGain = total_gain_loss_pct >= 0;
  const lineColor = isGain ? '#10b981' : '#ef4444'; // green-500 : red-500
  const bgColor = isGain ? 'bg-green-900/20' : 'bg-red-900/20';
  const textColor = isGain ? 'text-green-400' : 'text-red-400';

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Format date for axis
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    if (display_mode === 'weekly') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    return date.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' });
  };

  return (
    <div className="space-y-3">
      {/* Summary Header */}
      <div className={`flex justify-between items-center p-3 rounded-lg ${bgColor}`}>
        <div>
          <div className="text-xs text-gray-400">Current Value</div>
          <div className="text-lg font-semibold">{formatCurrency(current_value)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Starting Value</div>
          <div className="text-lg font-semibold">{formatCurrency(starting_value)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Gain/Loss</div>
          <div className={`text-lg font-semibold ${textColor}`}>
            {isGain ? '+' : ''}{total_gain_loss_pct.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Graph */}
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data_points}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="#9ca3af"
            fontSize={10}
            tickCount={display_mode === 'weekly' ? 6 : 8}
          />
          <YAxis
            tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
            stroke="#9ca3af"
            fontSize={10}
            width={50}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '4px',
              fontSize: '12px',
            }}
            labelFormatter={(dateStr) => new Date(dateStr).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            })}
            formatter={(value, name) => {
              if (name === 'total_value') {
                return [formatCurrency(value), 'Portfolio Value'];
              }
              return [`${value.toFixed(2)}%`, 'Change'];
            }}
          />
          <Line
            type="monotone"
            dataKey="total_value"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Display mode indicator */}
      <div className="text-xs text-gray-500 text-center">
        {display_mode === 'weekly' ? 'Weekly data points' : 'Daily data points'}
      </div>
    </div>
  );
}

export default PortfolioGraph;
