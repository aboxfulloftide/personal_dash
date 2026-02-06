import { useWidgetData } from '../../hooks/useWidgetData';

function formatTimeAgo(isoDate) {
  if (!isoDate) return '';

  try {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  } catch (e) {
    return '';
  }
}

function truncateText(text, maxLength = 150) {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}

function ArticleItem({ article }) {
  return (
    <article className="border-b border-gray-200 dark:border-gray-700 last:border-b-0 pb-3 mb-3 last:pb-0 last:mb-0">
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block hover:bg-gray-50 dark:hover:bg-gray-700/30 -mx-1 px-1 py-1 rounded transition-colors"
      >
        <div className="flex gap-3">
          {article.image_url && (
            <div className="flex-shrink-0 w-20 h-20 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden">
              <img
                src={article.image_url}
                alt=""
                className="w-full h-full object-cover"
                loading="lazy"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 leading-tight mb-1 line-clamp-2">
              {article.title}
            </h3>

            {article.description && (
              <p className="text-xs text-gray-600 dark:text-gray-400 leading-snug mb-1 line-clamp-2">
                {truncateText(article.description, 120)}
              </p>
            )}

            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
              <span className="font-medium">{article.source}</span>
              {article.published && (
                <>
                  <span>•</span>
                  <time>{formatTimeAgo(article.published)}</time>
                </>
              )}
              {article.author && (
                <>
                  <span>•</span>
                  <span className="truncate">{article.author}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </a>
    </article>
  );
}

export default function NewsWidget({ config }) {
  const { data, loading, error } = useWidgetData({
    endpoint: '/news',
    params: {
      source: config.source || 'bbc',
      custom_url: config.custom_url || undefined,
      max_articles: config.max_articles || 10,
      provider: config.provider || 'rss',
      api_key: config.api_key || undefined,
      category: config.category || 'general',
      include_keywords: config.include_keywords || undefined,
      exclude_keywords: config.exclude_keywords || undefined,
    },
    refreshInterval: config.refresh_interval || 600,
    enabled: true,
  });

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500 p-4">
        <span className="text-2xl mb-2">📰</span>
        <p className="text-sm text-center">{error}</p>
      </div>
    );
  }

  if (!data || !data.articles || data.articles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <span className="text-4xl mb-2">📰</span>
        <p className="text-sm">No articles found</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between mb-2 pb-2 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-lg">📰</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {data.source}
          </span>
        </div>
        {data.cached && (
          <span className="text-xs text-gray-400 dark:text-gray-500">cached</span>
        )}
      </div>

      {/* Articles list - scrollable */}
      <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
        {data.articles.map((article, index) => (
          <ArticleItem key={index} article={article} />
        ))}
      </div>
    </div>
  );
}
