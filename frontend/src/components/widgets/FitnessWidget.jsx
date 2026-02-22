import { useState, lazy, Suspense } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useWidgetData } from '../../hooks/useWidgetData';
import FitnessLogModal from './FitnessLogModal';

const GarminSetupModal = lazy(() => import('./GarminSetupModal'));

const ACTIVITY_ICONS = {
  running: '🏃',
  cycling: '🚴',
  swimming: '🏊',
  walking: '🚶',
  strength_training: '💪',
  yoga: '🧘',
  hiking: '🥾',
  tennis: '🎾',
  golf: '⛳',
  skiing: '⛷️',
  rowing: '🚣',
  elliptical: '🏃',
  cardio: '❤️',
  sport: '🏅',
  default: '🏋️',
};

function activityIcon(type) {
  if (!type) return ACTIVITY_ICONS.default;
  const lower = type.toLowerCase();
  for (const [key, icon] of Object.entries(ACTIVITY_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return ACTIVITY_ICONS.default;
}

function formatDuration(minutes) {
  if (!minutes) return '—';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

function formatSleep(minutes) {
  if (!minutes) return '—';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

function formatSteps(steps) {
  if (steps == null) return '—';
  return steps.toLocaleString();
}

export default function FitnessWidget({ config = {} }) {
  const unit = config.unit || 'lbs';
  const daysBack = config.days_back || 30;
  const refreshInterval = config.refresh_interval || 300;

  const [logModalOpen, setLogModalOpen] = useState(false);
  const [garminModalOpen, setGarminModalOpen] = useState(false);
  const [garminStatus, setGarminStatus] = useState(null);

  const { data, loading, error, refresh } = useWidgetData({
    endpoint: '/fitness/stats',
    params: { days: daysBack, unit },
    refreshInterval,
  });

  const handleWeightSaved = () => {
    refresh();
  };

  const handleGarminStatusChange = (newStatus) => {
    setGarminStatus(newStatus);
    refresh();
  };

  const currentGarminStatus = garminStatus ?? {
    connected: data?.garmin_connected,
    sync_status: data?.garmin_sync_status,
    last_synced_at: data?.garmin_last_synced_at,
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        Loading fitness data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-400">
        Failed to load fitness data: {error}
      </div>
    );
  }

  // Build weight chart data
  const weightHistory = data?.weight_history || [];
  const chartData = weightHistory.map((entry) => {
    let w = parseFloat(entry.weight);
    const entryUnit = entry.unit || 'lbs';
    if (entryUnit !== unit) {
      if (unit === 'kg' && entryUnit === 'lbs') w = Math.round(w * 0.453592 * 10) / 10;
      else if (unit === 'lbs' && entryUnit === 'kg') w = Math.round(w * 2.20462 * 10) / 10;
    }
    return {
      date: entry.recorded_at,
      weight: w,
    };
  });

  const weightValues = chartData.map((d) => d.weight).filter(Boolean);
  const minW = weightValues.length ? Math.min(...weightValues) : 0;
  const maxW = weightValues.length ? Math.max(...weightValues) : 0;
  const wRange = maxW - minW;
  const wPad = Math.max(wRange * 0.1, 1);
  const yDomain = [Math.floor(minW - wPad), Math.ceil(maxW + wPad)];

  const formatChartDate = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' });
  };

  const activities = data?.recent_activities || [];
  const isGarminConnected = data?.garmin_connected;
  const hasAnyData = isGarminConnected || weightHistory.length > 0;

  const syncStatusColor = {
    ok: 'text-green-400',
    error: 'text-red-400',
    never: 'text-gray-400',
  }[data?.garmin_sync_status] || 'text-gray-400';

  // First-run empty state
  if (!hasAnyData) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-4 text-center">
        <div className="text-4xl">🏋️</div>
        <div>
          <p className="text-sm font-medium text-gray-200 mb-1">Get started with Fitness Stats</p>
          <p className="text-xs text-gray-400 mb-4">
            Log your weight manually, or connect Garmin to automatically sync steps, sleep, heart rate, and workouts.
          </p>
          <div className="flex flex-col gap-2">
            <button
              onClick={() => setLogModalOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded"
            >
              + Log Weight
            </button>
            <button
              onClick={() => setGarminModalOpen(true)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded flex items-center justify-center gap-2"
            >
              <span>Connect Garmin</span>
              <span className="text-xs text-gray-400">(steps, sleep, HR, workouts)</span>
            </button>
          </div>
        </div>

        <FitnessLogModal
          isOpen={logModalOpen}
          onClose={() => setLogModalOpen(false)}
          onSaved={handleWeightSaved}
          defaultUnit={unit}
        />
        <Suspense fallback={null}>
          {garminModalOpen && (
            <GarminSetupModal
              isOpen={garminModalOpen}
              onClose={() => setGarminModalOpen(false)}
              garminStatus={currentGarminStatus}
              onStatusChange={handleGarminStatusChange}
            />
          )}
        </Suspense>
      </div>
    );
  }

  return (
    <div className="space-y-3 text-sm">
      {/* Today's stats row */}
      <div className="grid grid-cols-4 gap-1">
        <StatChip
          label="Steps"
          value={formatSteps(data?.today_steps)}
          icon="👟"
          active={data?.today_steps != null}
        />
        <StatChip
          label="Sleep"
          value={formatSleep(data?.today_sleep_minutes)}
          icon="😴"
          active={data?.today_sleep_minutes != null}
        />
        <StatChip
          label="Rest. HR"
          value={data?.today_resting_hr ? `${data.today_resting_hr} bpm` : '—'}
          icon="❤️"
          active={data?.today_resting_hr != null}
        />
        <StatChip
          label="Weight"
          value={data?.latest_weight ? `${data.latest_weight} ${data.latest_weight_unit}` : '—'}
          icon="⚖️"
          active={data?.latest_weight != null}
        />
      </div>

      {/* Weight Chart */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Weight ({unit})
          </span>
          <button
            onClick={() => setLogModalOpen(true)}
            className="text-xs px-2 py-0.5 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            + Log
          </button>
        </div>

        {chartData.length > 1 ? (
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="date"
                tickFormatter={formatChartDate}
                stroke="#9ca3af"
                fontSize={9}
                tickCount={6}
              />
              <YAxis
                domain={yDomain}
                stroke="#9ca3af"
                fontSize={9}
                width={45}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  fontSize: '11px',
                }}
                labelFormatter={(d) => new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
                  month: 'short', day: 'numeric', year: 'numeric',
                })}
                formatter={(v) => [`${v} ${unit}`, 'Weight']}
              />
              <Line
                type="monotone"
                dataKey="weight"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 2 }}
                activeDot={{ r: 4 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-20 flex items-center justify-center text-gray-500 text-xs">
            {chartData.length === 1
              ? `1 entry — log more to see a chart`
              : 'No weight entries yet — click "+ Log" to start'}
          </div>
        )}
      </div>

      {/* Recent Activities — only shown when Garmin connected */}
      {isGarminConnected && (
        <div>
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Recent Activities
          </span>
          {activities.length > 0 ? (
            <div className="mt-1 space-y-1">
              {activities.slice(0, 5).map((act) => (
                <div key={act.id} className="flex items-center gap-2 py-1 px-2 rounded bg-gray-700/30 hover:bg-gray-700/50">
                  <span className="text-base flex-shrink-0">{activityIcon(act.activity_type)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="truncate text-gray-200 text-xs font-medium">
                      {act.name || act.activity_type || 'Workout'}
                    </div>
                    <div className="text-gray-500 text-xs">
                      {act.start_time ? new Date(act.start_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0 text-xs text-gray-400">
                    <div>{formatDuration(act.duration_minutes)}</div>
                    {act.calories ? <div>{act.calories} cal</div> : null}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-1 text-xs text-gray-500">
              No activities in the last {daysBack} days
            </div>
          )}
        </div>
      )}

      {/* Garmin footer */}
      <div className="flex items-center justify-between pt-1 border-t border-gray-700/50">
        {isGarminConnected ? (
          <span className={`text-xs ${syncStatusColor}`}>
            Garmin {data?.garmin_sync_status === 'ok' ? '✓ synced' : data?.garmin_sync_status === 'error' ? '⚠ sync error' : '— never synced'}
          </span>
        ) : (
          <button
            onClick={() => setGarminModalOpen(true)}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            + Connect Garmin for steps, sleep & workouts
          </button>
        )}
        {isGarminConnected && (
          <button
            onClick={() => setGarminModalOpen(true)}
            className="text-xs px-2 py-0.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
          >
            Garmin Settings
          </button>
        )}
      </div>

      {/* Modals */}
      <FitnessLogModal
        isOpen={logModalOpen}
        onClose={() => setLogModalOpen(false)}
        onSaved={handleWeightSaved}
        defaultUnit={unit}
      />

      <Suspense fallback={null}>
        {garminModalOpen && (
          <GarminSetupModal
            isOpen={garminModalOpen}
            onClose={() => setGarminModalOpen(false)}
            garminStatus={currentGarminStatus}
            onStatusChange={handleGarminStatusChange}
          />
        )}
      </Suspense>
    </div>
  );
}

function StatChip({ label, value, icon, active }) {
  return (
    <div className={`flex flex-col items-center p-2 rounded-lg text-center ${
      active ? 'bg-gray-700/50' : 'bg-gray-800/30'
    }`}>
      <span className="text-base mb-0.5">{icon}</span>
      <span className="text-xs font-semibold text-gray-200 leading-tight">{value}</span>
      <span className="text-xs text-gray-500 leading-tight">{label}</span>
    </div>
  );
}
