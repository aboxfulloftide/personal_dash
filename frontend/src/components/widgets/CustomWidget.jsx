import { useState } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';
import CustomWidgetManageModal from './CustomWidgetManageModal';

const COLOR_BORDER = {
  red: 'border-l-4 border-red-500',
  yellow: 'border-l-4 border-yellow-500',
  green: 'border-l-4 border-green-500',
  blue: 'border-l-4 border-blue-500',
};

const COLOR_TEXT = {
  red: 'text-red-600 dark:text-red-400',
  yellow: 'text-yellow-600 dark:text-yellow-400',
  green: 'text-green-600 dark:text-green-400',
  blue: 'text-blue-600 dark:text-blue-400',
};

const HIGHLIGHT_BG = 'bg-yellow-50 dark:bg-yellow-900/20';
const DEFAULT_BG = 'bg-gray-50 dark:bg-gray-700/40';

function itemBg(item) {
  return item.highlight ? HIGHLIGHT_BG : DEFAULT_BG;
}

function itemColor(item) {
  return item.color ? COLOR_BORDER[item.color] || '' : '';
}

function PencilIcon() {
  return (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
    </svg>
  );
}

function ListView({ items }) {
  return (
    <ul className="space-y-1">
      {items.map((item) => (
        <li
          key={item.id}
          className={`rounded px-2 py-1.5 ${itemBg(item)} ${itemColor(item)}`}
        >
          <div className="flex items-start justify-between gap-1">
            <div className="flex items-start gap-1.5 min-w-0">
              {item.icon && (
                <span className="flex-shrink-0 text-sm leading-tight mt-0.5">{item.icon}</span>
              )}
              <div className="min-w-0">
                <div className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate leading-tight">
                  {item.title}
                  {item.subtitle && (
                    <span className="font-normal text-gray-500 dark:text-gray-400">
                      {' — '}{item.subtitle}
                    </span>
                  )}
                </div>
                {item.description && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {item.description}
                  </div>
                )}
              </div>
            </div>
            {item.link_url && (
              <a
                href={item.link_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 text-xs text-blue-500 hover:text-blue-600 dark:text-blue-400 whitespace-nowrap"
                title={item.link_url}
              >
                {item.link_text || '→'}
              </a>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

function CompactView({ items }) {
  return (
    <ul className="space-y-0.5">
      {items.map((item) => {
        const inner = (
          <div className="flex items-center gap-1.5 min-w-0">
            {item.icon && (
              <span className="flex-shrink-0 text-sm">{item.icon}</span>
            )}
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
              {item.title}
            </span>
          </div>
        );
        return (
          <li
            key={item.id}
            className={`rounded px-2 py-1 ${itemBg(item)} ${itemColor(item)}`}
          >
            {item.link_url ? (
              <a
                href={item.link_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-1 hover:opacity-80"
                title={item.subtitle || item.link_url}
              >
                {inner}
                <span className="flex-shrink-0 text-xs text-blue-500 dark:text-blue-400">
                  {item.link_text || '→'}
                </span>
              </a>
            ) : (
              inner
            )}
          </li>
        );
      })}
    </ul>
  );
}

function TableView({ items }) {
  return (
    <table className="w-full text-sm border-collapse">
      <tbody>
        {items.map((item) => (
          <tr
            key={item.id}
            className={`border-b border-gray-200 dark:border-gray-700 last:border-0 ${item.highlight ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''}`}
          >
            <td className="py-1.5 pr-2 max-w-0 w-1/2">
              <div className="flex items-center gap-1.5 truncate">
                {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
                <span
                  className="font-medium text-gray-800 dark:text-gray-200 truncate"
                  title={item.description || undefined}
                >
                  {item.title}
                </span>
              </div>
            </td>
            <td className="py-1.5 text-right max-w-0 w-1/2">
              {item.link_url ? (
                <a
                  href={item.link_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-600 dark:text-blue-400 truncate block"
                  title={item.link_url}
                >
                  {item.subtitle || item.link_text || '→'}
                </a>
              ) : (
                <span className={`truncate block ${item.color ? COLOR_TEXT[item.color] || 'text-gray-500 dark:text-gray-400' : 'text-gray-500 dark:text-gray-400'}`}>
                  {item.subtitle || '—'}
                </span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function GridView({ items }) {
  return (
    <div className="grid grid-cols-2 gap-1.5">
      {items.map((item) => {
        const card = (
          <div className={`rounded p-2 h-full ${itemBg(item)} ${itemColor(item)}`}>
            <div className="flex items-center gap-1 min-w-0 mb-0.5">
              {item.icon && <span className="flex-shrink-0 text-sm">{item.icon}</span>}
              <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate leading-tight">
                {item.title}
              </span>
            </div>
            {item.subtitle && (
              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {item.subtitle}
              </div>
            )}
          </div>
        );

        return item.link_url ? (
          <a
            key={item.id}
            href={item.link_url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:opacity-80"
            title={item.link_url}
          >
            {card}
          </a>
        ) : (
          <div key={item.id}>{card}</div>
        );
      })}
    </div>
  );
}

const VIEWS = {
  list: ListView,
  compact: CompactView,
  table: TableView,
  grid: GridView,
};

export default function CustomWidget({ config = {}, widgetId }) {
  const [showManage, setShowManage] = useState(false);

  const maxItems = config.max_items || 10;
  const refreshInterval = config.refresh_interval || 60;
  const displayMode = config.display_mode || 'list';

  const { data, loading, error, refetch } = useWidgetData({
    endpoint: widgetId ? `/custom-widgets/${widgetId}/items?max_items=${maxItems}` : null,
    refreshInterval,
  });

  if (!widgetId) {
    return (
      <div className="text-center text-gray-400 dark:text-gray-500 py-8 text-sm">
        Widget ID not available
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-gray-500 dark:text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 dark:text-red-400 text-sm p-2">
        Failed to load items
      </div>
    );
  }

  const items = data?.items || [];
  const ItemsView = VIEWS[displayMode] || ListView;

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto scrollbar-hide">
        {items.length === 0 ? (
          <div className="text-center text-gray-400 dark:text-gray-500 py-8">
            <div className="text-3xl mb-2">📋</div>
            <div className="text-sm">No items yet</div>
            <button
              onClick={() => setShowManage(true)}
              className="mt-2 text-xs text-blue-500 hover:underline"
            >
              Add items
            </button>
          </div>
        ) : (
          <ItemsView items={items} />
        )}
      </div>

      <div className="flex-shrink-0 pt-2 mt-1 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setShowManage(true)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <PencilIcon />
          Manage Items
        </button>
      </div>

      {showManage && (
        <CustomWidgetManageModal
          widgetId={widgetId}
          onClose={() => {
            setShowManage(false);
            refetch();
          }}
        />
      )}
    </div>
  );
}
