import asyncio
import httpx
import feedparser
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.api.v1.deps import CurrentActiveUser

router = APIRouter(prefix="/news", tags=["News"])


class NewsArticle(BaseModel):
    title: str
    description: str | None
    url: str
    source: str
    published: str | None
    author: str | None
    image_url: str | None


class NewsResponse(BaseModel):
    articles: list[NewsArticle]
    source: str
    cached: bool = False


# Predefined RSS sources
RSS_SOURCES = {
    "bbc": {
        "name": "BBC News",
        "url": "http://feeds.bbci.co.uk/news/rss.xml",
    },
    "npr": {
        "name": "NPR News",
        "url": "https://feeds.npr.org/1001/rss.xml",
    },
    "reuters": {
        "name": "Reuters",
        "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    },
    "cnn": {
        "name": "CNN Top Stories",
        "url": "http://rss.cnn.com/rss/cnn_topstories.rss",
    },
    "techcrunch": {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
    },
    "hackernews": {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
    },
}


# In-memory cache
_news_cache: dict[str, tuple[NewsResponse, datetime]] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes


def get_cache_key(
    source: str,
    custom_url: str | None,
    provider: str,
    include_keywords: str | None = None,
    exclude_keywords: str | None = None,
) -> str:
    """Generate cache key from parameters."""
    base_key = ""
    if provider == "rss":
        if source == "custom" and custom_url:
            base_key = f"rss_custom_{custom_url}"
        else:
            base_key = f"rss_{source}"
    else:
        base_key = f"newsapi_{source}"

    # Add keywords to cache key if present
    if include_keywords:
        base_key += f"_inc_{include_keywords.replace(',', '_')}"
    if exclude_keywords:
        base_key += f"_exc_{exclude_keywords.replace(',', '_')}"

    return base_key


def get_cached_news(cache_key: str) -> NewsResponse | None:
    """Get news from cache if not expired."""
    if cache_key in _news_cache:
        cached_response, cached_time = _news_cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=CACHE_TTL_SECONDS):
            cached_response.cached = True
            return cached_response
        # Expired, remove from cache
        del _news_cache[cache_key]
    return None


def cache_news(cache_key: str, response: NewsResponse):
    """Store news in cache."""
    _news_cache[cache_key] = (response, datetime.now())


async def fetch_rss_feed(url: str, source_name: str, max_articles: int) -> list[NewsArticle]:
    """Fetch and parse RSS feed."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0, follow_redirects=True)
            resp.raise_for_status()
            content = resp.text
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="RSS feed request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch RSS feed: {str(e)}")

    try:
        feed = feedparser.parse(content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse RSS feed: {str(e)}")

    if feed.bozo and not feed.entries:
        raise HTTPException(status_code=502, detail="Invalid or empty RSS feed")

    articles = []
    for entry in feed.entries[:max_articles]:
        # Parse published date
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published = datetime(*entry.updated_parsed[:6]).isoformat()
            except (TypeError, ValueError):
                pass

        # Get description
        description = None
        if hasattr(entry, "summary"):
            description = entry.summary
        elif hasattr(entry, "description"):
            description = entry.description

        # Get image URL
        image_url = None
        if hasattr(entry, "media_content") and entry.media_content:
            image_url = entry.media_content[0].get("url")
        elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get("url")
        elif hasattr(entry, "enclosures") and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get("type", "").startswith("image/"):
                    image_url = enclosure.get("href")
                    break

        # Get author
        author = None
        if hasattr(entry, "author"):
            author = entry.author
        elif hasattr(entry, "author_detail") and entry.author_detail:
            author = entry.author_detail.get("name")

        articles.append(NewsArticle(
            title=entry.title if hasattr(entry, "title") else "Untitled",
            description=description,
            url=entry.link if hasattr(entry, "link") else "",
            source=source_name,
            published=published,
            author=author,
            image_url=image_url,
        ))

    return articles


def filter_articles(
    articles: list[NewsArticle],
    include_keywords: str | None = None,
    exclude_keywords: str | None = None,
) -> list[NewsArticle]:
    """Filter articles by include/exclude keywords (case-insensitive)."""
    if not include_keywords and not exclude_keywords:
        return articles

    # Parse keywords
    include_list = [k.strip().lower() for k in include_keywords.split(",")] if include_keywords else []
    exclude_list = [k.strip().lower() for k in exclude_keywords.split(",")] if exclude_keywords else []

    filtered = []
    for article in articles:
        # Combine searchable text (title + description)
        searchable_text = (
            f"{article.title or ''} {article.description or ''}"
        ).lower()

        # Check exclude keywords first (higher priority)
        if exclude_list:
            if any(keyword in searchable_text for keyword in exclude_list):
                continue

        # Check include keywords
        if include_list:
            if not any(keyword in searchable_text for keyword in include_list):
                continue

        filtered.append(article)

    return filtered


async def fetch_newsapi(
    api_key: str,
    category: str,
    max_articles: int,
    country: str = "us",
) -> list[NewsArticle]:
    """Fetch news from NewsAPI.org."""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key required for NewsAPI")

    url = (
        f"https://newsapi.org/v2/top-headlines?"
        f"country={country}&category={category}&pageSize={max_articles}&apiKey={api_key}"
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)

            if resp.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid NewsAPI key")
            elif resp.status_code == 429:
                raise HTTPException(status_code=429, detail="NewsAPI rate limit exceeded")

            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="NewsAPI request timed out")
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch from NewsAPI: {str(e)}")

    if data.get("status") != "ok":
        raise HTTPException(status_code=502, detail=data.get("message", "NewsAPI error"))

    articles = []
    for item in data.get("articles", [])[:max_articles]:
        articles.append(NewsArticle(
            title=item.get("title", "Untitled"),
            description=item.get("description"),
            url=item.get("url", ""),
            source=item.get("source", {}).get("name", "Unknown"),
            published=item.get("publishedAt"),
            author=item.get("author"),
            image_url=item.get("urlToImage"),
        ))

    return articles


@router.get("", response_model=NewsResponse)
async def get_news(
    current_user: CurrentActiveUser,
    source: str = Query("bbc", description="Comma-separated news source IDs or 'custom'"),
    custom_url: Optional[str] = Query(None, description="Custom RSS feed URL"),
    max_articles: int = Query(10, ge=5, le=50, description="Number of articles"),
    provider: str = Query("rss", description="Provider: 'rss' or 'newsapi'"),
    api_key: Optional[str] = Query(None, description="API key for NewsAPI"),
    category: str = Query("general", description="NewsAPI category"),
    include_keywords: Optional[str] = Query(None, description="Comma-separated keywords to include"),
    exclude_keywords: Optional[str] = Query(None, description="Comma-separated keywords to exclude"),
):
    """Fetch news headlines from RSS feeds or NewsAPI.org with optional keyword filtering.

    Supports multiple sources by passing comma-separated source IDs (e.g., 'bbc,techcrunch,npr').
    Articles from all sources are merged and sorted by published date.
    """

    # Generate cache key (includes keywords for separate caching)
    cache_key = get_cache_key(source, custom_url, provider, include_keywords, exclude_keywords)

    # Check cache
    cached = get_cached_news(cache_key)
    if cached:
        return cached

    # Parse sources (comma-separated)
    source_ids = [s.strip() for s in source.split(",") if s.strip()]
    if not source_ids:
        raise HTTPException(status_code=400, detail="At least one source required")

    # Fetch more articles if filtering is enabled to ensure we have enough after filtering
    fetch_count_per_source = max_articles
    if include_keywords or exclude_keywords:
        fetch_count_per_source = min(max_articles * 3, 50)  # Fetch up to 3x more, max 50

    # For multiple sources, adjust per-source count to get enough total articles
    if len(source_ids) > 1:
        fetch_count_per_source = max(10, fetch_count_per_source // len(source_ids))

    all_articles = []
    source_names = []

    try:
        if provider == "rss":
            # Fetch from all sources in parallel
            tasks = []
            for source_id in source_ids:
                if source_id == "custom":
                    if not custom_url:
                        raise HTTPException(status_code=400, detail="custom_url required for custom source")
                    tasks.append(fetch_rss_feed(custom_url, "Custom Feed", fetch_count_per_source))
                    source_names.append("Custom Feed")
                else:
                    if source_id not in RSS_SOURCES:
                        raise HTTPException(status_code=400, detail=f"Unknown source: {source_id}")
                    source_info = RSS_SOURCES[source_id]
                    tasks.append(fetch_rss_feed(source_info["url"], source_info["name"], fetch_count_per_source))
                    source_names.append(source_info["name"])

            # Fetch all sources in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect articles from successful fetches
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Log error but continue with other sources
                    continue
                all_articles.extend(result)

        elif provider == "newsapi":
            source_names.append(f"NewsAPI - {category.capitalize()}")
            all_articles = await fetch_newsapi(api_key or "", category, fetch_count_per_source)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch news: {str(e)}")

    # Sort articles by published date (most recent first)
    def get_published_time(article: NewsArticle) -> datetime:
        """Extract datetime from article, use epoch if no date."""
        if article.published:
            try:
                return datetime.fromisoformat(article.published.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        return datetime.min  # Put undated articles at the end

    all_articles.sort(key=get_published_time, reverse=True)

    # Apply keyword filtering
    if include_keywords or exclude_keywords:
        all_articles = filter_articles(all_articles, include_keywords, exclude_keywords)

    # Limit to requested max_articles after filtering
    all_articles = all_articles[:max_articles]

    if not all_articles:
        raise HTTPException(status_code=404, detail="No articles found matching criteria")

    # Generate display name for sources
    if len(source_names) == 1:
        display_name = source_names[0]
    else:
        display_name = f"{len(source_names)} sources"

    response = NewsResponse(
        articles=all_articles,
        source=display_name,
        cached=False,
    )

    # Cache the response
    cache_news(cache_key, response)

    return response
