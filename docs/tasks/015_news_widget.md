# Task 015: News Widget

## Objective
Build a news widget that displays headlines from various sources using free RSS feeds, with category filtering and source management.

## Prerequisites
- Task 006 completed (Widget Framework)
- Task 003 completed (Database Schema)

## Features
- Display news headlines from RSS feeds
- Multiple news source support
- Category/topic filtering
- Click to open full article
- Auto-refresh with caching
- Source management (add/remove feeds)
- Compact and expanded view modes

## API Approach
- **RSS Feeds**: Free, no API key needed
- Major news outlets provide RSS feeds
- Can aggregate multiple sources

## Deliverables

### 1. Database Models

#### backend/app/models/news.py:
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class NewsSource(Base):
    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(100), nullable=False)
    feed_url = Column(String(500), nullable=False)
    category = Column(String(50), default="general")  # tech, business, sports, etc.

    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime, nullable=True)
    fetch_error = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="news_sources")


class CachedArticle(Base):
    __tablename__ = "cached_articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("news_sources.id"), nullable=False)

    guid = Column(String(500), nullable=False)  # Unique identifier from feed
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=True)

    fetched_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("NewsSource")
```

### 2. News Service

#### backend/app/services/news_service.py:
```python
import httpx
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime
import re

from sqlalchemy.orm import Session
from app.models.news import NewsSource, CachedArticle


# Popular free RSS feeds
DEFAULT_FEEDS = {
    "tech": [
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
    ],
    "business": [
        {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance"},
        {"name": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss"},
    ],
    "general": [
        {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/rss.xml"},
        {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml"},
        {"name": "Reuters Top News", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best"},
    ],
    "science": [
        {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
        {"name": "Science Daily", "url": "https://www.sciencedaily.com/rss/all.xml"},
    ]
}


class NewsService:
    CACHE_DURATION = timedelta(minutes=15)

    async def fetch_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse an RSS feed."""

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                timeout=15,
                follow_redirects=True,
                headers={"User-Agent": "PersonalDash/1.0"}
            )
            response.raise_for_status()
            content = response.text

        feed = feedparser.parse(content)
        articles = []

        for entry in feed.entries[:20]:  # Limit to 20 articles per feed
            article = self._parse_entry(entry)
            if article:
                articles.append(article)

        return articles

    def _parse_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Parse a feed entry into article dict."""

        try:
            # Get title
            title = entry.get('title', '').strip()
            if not title:
                return None

            # Get link
            link = entry.get('link', '')
            if not link:
                return None

            # Get description
            description = entry.get('summary', entry.get('description', ''))
            if description:
                # Strip HTML tags
                description = re.sub(r'<[^>]+>', '', description)
                description = description[:500]  # Limit length

            # Get published date
            published = None
            if entry.get('published_parsed'):
                try:
                    published = datetime(*entry.published_parsed[:6])
                except:
                    pass
            elif entry.get('published'):
                try:
                    published = parsedate_to_datetime(entry.published)
                except:
                    pass

            # Get image
            image_url = None
            if entry.get('media_content'):
                for media in entry.media_content:
                    if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                        image_url = media.get('url')
                        break
            if not image_url and entry.get('media_thumbnail'):
                image_url = entry.media_thumbnail[0].get('url')

            # Try to extract image from content
            if not image_url:
                content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                img_match = re.search(r'<img[^>]+src=["']([^"']+)["']', content)
                if img_match:
                    image_url = img_match.group(1)

            return {
                "guid": entry.get('id', entry.get('link', '')),
                "title": title,
                "link": link,
                "description": description,
                "image_url": image_url,
                "published_at": published
            }
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None

    async def refresh_source(
        self, 
        db: Session, 
        source: NewsSource
    ) -> Dict[str, Any]:
        """Refresh articles from a news source."""

        try:
            articles = await self.fetch_feed(source.feed_url)

            # Clear old articles for this source
            db.query(CachedArticle).filter(
                CachedArticle.source_id == source.id
            ).delete()

            # Add new articles
            for article_data in articles:
                article = CachedArticle(
                    source_id=source.id,
                    **article_data
                )
                db.add(article)

            source.last_fetched = datetime.utcnow()
            source.fetch_error = None
            db.commit()

            return {"success": True, "articles": len(articles)}

        except Exception as e:
            source.fetch_error = str(e)[:500]
            db.commit()
            return {"error": str(e)}

    async def get_articles(
        self,
        db: Session,
        user_id: int,
        category: Optional[str] = None,
        source_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get cached articles for user."""

        # Check if refresh needed
        sources = db.query(NewsSource).filter(
            NewsSource.user_id == user_id,
            NewsSource.is_active == True
        ).all()

        if category:
            sources = [s for s in sources if s.category == category]

        if source_ids:
            sources = [s for s in sources if s.id in source_ids]

        # Refresh stale sources
        for source in sources:
            if not source.last_fetched or                datetime.utcnow() - source.last_fetched > self.CACHE_DURATION:
                await self.refresh_source(db, source)

        # Get articles
        query = db.query(CachedArticle).join(NewsSource).filter(
            NewsSource.user_id == user_id,
            NewsSource.is_active == True
        )

        if category:
            query = query.filter(NewsSource.category == category)

        if source_ids:
            query = query.filter(NewsSource.id.in_(source_ids))

        articles = query.order_by(
            CachedArticle.published_at.desc().nullslast()
        ).limit(limit).all()

        return [self._article_to_dict(a) for a in articles]

    def _article_to_dict(self, article: CachedArticle) -> Dict[str, Any]:
        return {
            "id": article.id,
            "source_id": article.source_id,
            "source_name": article.source.name if article.source else "Unknown",
            "category": article.source.category if article.source else "general",
            "title": article.title,
            "link": article.link,
            "description": article.description,
            "image_url": article.image_url,
            "published_at": article.published_at.isoformat() if article.published_at else None
        }

    def get_default_feeds(self) -> Dict[str, List[Dict]]:
        """Get list of default feeds by category."""
        return DEFAULT_FEEDS
```

### 3. API Endpoints

#### backend/app/api/v1/news.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.news import NewsSource
from app.schemas.news import (
    NewsSourceCreate, NewsSourceResponse, ArticleResponse
)
from app.api.deps import get_current_user
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])
news_service = NewsService()


@router.get("/sources", response_model=List[NewsSourceResponse])
async def list_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's news sources."""
    sources = db.query(NewsSource).filter(
        NewsSource.user_id == current_user.id
    ).all()
    return sources


@router.post("/sources", response_model=NewsSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_source(
    source_data: NewsSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a news source."""

    # Check limit
    count = db.query(NewsSource).filter(
        NewsSource.user_id == current_user.id
    ).count()

    if count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 news sources allowed"
        )

    source = NewsSource(
        user_id=current_user.id,
        name=source_data.name,
        feed_url=source_data.feed_url,
        category=source_data.category or "general"
    )

    db.add(source)
    db.commit()
    db.refresh(source)

    # Initial fetch
    await news_service.refresh_source(db, source)
    db.refresh(source)

    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a news source."""

    source = db.query(NewsSource).filter(
        NewsSource.id == source_id,
        NewsSource.user_id == current_user.id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()


@router.post("/sources/{source_id}/refresh")
async def refresh_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh a news source."""

    source = db.query(NewsSource).filter(
        NewsSource.id == source_id,
        NewsSource.user_id == current_user.id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await news_service.refresh_source(db, source)
    return result


@router.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get news articles."""

    articles = await news_service.get_articles(
        db, current_user.id, category=category, limit=limit
    )
    return articles


@router.get("/defaults")
async def get_default_feeds():
    """Get list of default/suggested RSS feeds."""
    return news_service.get_default_feeds()


@router.post("/sources/add-defaults")
async def add_default_sources(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add all default sources for a category."""

    defaults = news_service.get_default_feeds()

    if category not in defaults:
        raise HTTPException(status_code=400, detail="Invalid category")

    added = 0
    for feed in defaults[category]:
        # Check if already exists
        exists = db.query(NewsSource).filter(
            NewsSource.user_id == current_user.id,
            NewsSource.feed_url == feed["url"]
        ).first()

        if not exists:
            source = NewsSource(
                user_id=current_user.id,
                name=feed["name"],
                feed_url=feed["url"],
                category=category
            )
            db.add(source)
            added += 1

    db.commit()

    return {"added": added}
```

### 4. Pydantic Schemas

#### backend/app/schemas/news.py:
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class NewsSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    feed_url: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=50)


class NewsSourceResponse(BaseModel):
    id: int
    name: str
    feed_url: str
    category: str
    is_active: bool
    last_fetched: Optional[datetime]
    fetch_error: Optional[str]

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    category: str
    title: str
    link: str
    description: Optional[str]
    image_url: Optional[str]
    published_at: Optional[str]
```

### 5. Frontend News Widget

#### frontend/src/components/widgets/NewsWidget.jsx:
```jsx
import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, Settings, ExternalLink, ChevronDown,
  Newspaper, Clock
} from 'lucide-react';
import { useNews } from '../../hooks/useNews';

const CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'tech', label: 'Tech' },
  { id: 'business', label: 'Business' },
  { id: 'general', label: 'General' },
  { id: 'science', label: 'Science' }
];

export default function NewsWidget({ config }) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('compact'); // 'compact' or 'expanded'
  const [showSettings, setShowSettings] = useState(false);

  const { 
    articles, 
    sources, 
    defaultFeeds,
    loading, 
    fetchArticles,
    fetchSources,
    addSource,
    addDefaultSources,
    deleteSource
  } = useNews();

  useEffect(() => {
    fetchSources();
    fetchArticles(selectedCategory === 'all' ? null : selectedCategory);
  }, [selectedCategory]);

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;

    if (diff < 3600000) {
      const mins = Math.floor(diff / 60000);
      return `${mins}m ago`;
    } else if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    } else {
      const days = Math.floor(diff / 86400000);
      return `${days}d ago`;
    }
  };

  const handleRefresh = () => {
    fetchArticles(selectedCategory === 'all' ? null : selectedCategory);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-gray-500" />
          <span className="font-medium">News</span>
        </div>

        <div className="flex gap-1">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-1 mb-3 overflow-x-auto pb-1">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-2 py-1 text-xs rounded whitespace-nowrap ${
              selectedCategory === cat.id
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Articles List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {sources.length === 0 ? (
          <div className="text-center py-8">
            <Newspaper className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500 mb-3">No news sources added</p>
            <button
              onClick={() => setShowSettings(true)}
              className="text-sm text-blue-500 hover:underline"
            >
              Add news sources
            </button>
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {loading ? 'Loading...' : 'No articles found'}
          </div>
        ) : (
          articles.map((article) => (
            <ArticleCard 
              key={article.id} 
              article={article} 
              compact={viewMode === 'compact'}
              formatTime={formatTime}
            />
          ))
        )}
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <NewsSettingsModal
          sources={sources}
          defaultFeeds={defaultFeeds}
          onAddSource={addSource}
          onAddDefaults={addDefaultSources}
          onDeleteSource={deleteSource}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

function ArticleCard({ article, compact, formatTime }) {
  return (
    <a
      href={article.link}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-2 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-colors"
    >
      <div className="flex gap-3">
        {/* Thumbnail */}
        {!compact && article.image_url && (
          <div className="flex-shrink-0">
            <img
              src={article.image_url}
              alt=""
              className="w-16 h-16 object-cover rounded"
              onError={(e) => e.target.style.display = 'none'}
            />
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Title */}
          <h4 className="text-sm font-medium line-clamp-2 mb-1">
            {article.title}
          </h4>

          {/* Description */}
          {!compact && article.description && (
            <p className="text-xs text-gray-600 line-clamp-2 mb-1">
              {article.description}
            </p>
          )}

          {/* Meta */}
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span className="truncate">{article.source_name}</span>
            {article.published_at && (
              <>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTime(article.published_at)}
                </span>
              </>
            )}
          </div>
        </div>

        <ExternalLink className="w-3 h-3 text-gray-300 flex-shrink-0" />
      </div>
    </a>
  );
}

function NewsSettingsModal({ sources, defaultFeeds, onAddSource, onAddDefaults, onDeleteSource, onClose }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSource, setNewSource] = useState({ name: '', feed_url: '', category: 'general' });
  const [activeTab, setActiveTab] = useState('sources');

  const handleAdd = async () => {
    if (newSource.name && newSource.feed_url) {
      await onAddSource(newSource);
      setNewSource({ name: '', feed_url: '', category: 'general' });
      setShowAddForm(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">News Settings</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('sources')}
            className={`px-3 py-1 text-sm rounded ${
              activeTab === 'sources' ? 'bg-blue-500 text-white' : 'bg-gray-100'
            }`}
          >
            My Sources ({sources.length})
          </button>
          <button
            onClick={() => setActiveTab('discover')}
            className={`px-3 py-1 text-sm rounded ${
              activeTab === 'discover' ? 'bg-blue-500 text-white' : 'bg-gray-100'
            }`}
          >
            Discover
          </button>
        </div>

        {activeTab === 'sources' ? (
          <>
            {/* Current Sources */}
            {sources.length === 0 ? (
              <p className="text-sm text-gray-500 mb-4">No sources added yet</p>
            ) : (
              <div className="space-y-2 mb-4">
                {sources.map((source) => (
                  <div key={source.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <div className="text-sm font-medium">{source.name}</div>
                      <div className="text-xs text-gray-500">{source.category}</div>
                    </div>
                    <button
                      onClick={() => onDeleteSource(source.id)}
                      className="text-red-500 hover:text-red-700 text-xs"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add Custom Source */}
            {!showAddForm ? (
              <button
                onClick={() => setShowAddForm(true)}
                className="w-full p-2 border-2 border-dashed rounded text-gray-500 hover:border-blue-500 hover:text-blue-500 text-sm"
              >
                + Add Custom RSS Feed
              </button>
            ) : (
              <div className="p-3 border rounded space-y-3">
                <input
                  type="text"
                  placeholder="Source name"
                  value={newSource.name}
                  onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                  className="w-full p-2 border rounded text-sm"
                />
                <input
                  type="url"
                  placeholder="RSS Feed URL"
                  value={newSource.feed_url}
                  onChange={(e) => setNewSource({ ...newSource, feed_url: e.target.value })}
                  className="w-full p-2 border rounded text-sm"
                />
                <select
                  value={newSource.category}
                  onChange={(e) => setNewSource({ ...newSource, category: e.target.value })}
                  className="w-full p-2 border rounded text-sm"
                >
                  <option value="general">General</option>
                  <option value="tech">Tech</option>
                  <option value="business">Business</option>
                  <option value="science">Science</option>
                </select>
                <div className="flex gap-2">
                  <button
                    onClick={handleAdd}
                    className="flex-1 bg-blue-500 text-white py-2 rounded text-sm hover:bg-blue-600"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="flex-1 bg-gray-100 py-2 rounded text-sm hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          /* Discover Tab */
          <div className="space-y-4">
            {Object.entries(defaultFeeds).map(([category, feeds]) => (
              <div key={category}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium capitalize">{category}</h4>
                  <button
                    onClick={() => onAddDefaults(category)}
                    className="text-xs text-blue-500 hover:underline"
                  >
                    Add all
                  </button>
                </div>
                <div className="space-y-1">
                  {feeds.map((feed, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                      <span>{feed.name}</span>
                      <button
                        onClick={() => onAddSource({
                          name: feed.name,
                          feed_url: feed.url,
                          category
                        })}
                        className="text-blue-500 hover:underline text-xs"
                      >
                        Add
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### 6. React Hook

#### frontend/src/hooks/useNews.js:
```javascript
import { useState, useCallback } from 'react';
import api from '../services/api';

export function useNews() {
  const [articles, setArticles] = useState([]);
  const [sources, setSources] = useState([]);
  const [defaultFeeds, setDefaultFeeds] = useState({});
  const [loading, setLoading] = useState(false);

  const fetchSources = useCallback(async () => {
    try {
      const response = await api.get('/news/sources');
      setSources(response.data);
    } catch (err) {
      console.error('Failed to fetch news sources:', err);
    }
  }, []);

  const fetchArticles = useCallback(async (category = null) => {
    try {
      setLoading(true);
      const params = category ? { category } : {};
      const response = await api.get('/news/articles', { params });
      setArticles(response.data);
    } catch (err) {
      console.error('Failed to fetch articles:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDefaultFeeds = useCallback(async () => {
    try {
      const response = await api.get('/news/defaults');
      setDefaultFeeds(response.data);
    } catch (err) {
      console.error('Failed to fetch default feeds:', err);
    }
  }, []);

  const addSource = async (sourceData) => {
    try {
      const response = await api.post('/news/sources', sourceData);
      setSources(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const addDefaultSources = async (category) => {
    try {
      await api.post(`/news/sources/add-defaults?category=${category}`);
      await fetchSources();
    } catch (err) {
      throw err;
    }
  };

  const deleteSource = async (sourceId) => {
    try {
      await api.delete(`/news/sources/${sourceId}`);
      setSources(prev => prev.filter(s => s.id !== sourceId));
    } catch (err) {
      throw err;
    }
  };

  // Fetch default feeds on first call
  useState(() => {
    fetchDefaultFeeds();
  }, []);

  return {
    articles,
    sources,
    defaultFeeds,
    loading,
    fetchSources,
    fetchArticles,
    addSource,
    addDefaultSources,
    deleteSource
  };
}
```

## Dependencies to Add

### backend/requirements.txt (additions):
```
feedparser>=6.0.0
```

## Unit Tests

### tests/test_news_service.py:
```python
import pytest
from app.services.news_service import NewsService

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Test Article 1</title>
      <link>https://example.com/article1</link>
      <description>This is a test article</description>
      <pubDate>Mon, 15 Jan 2024 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Test Article 2</title>
      <link>https://example.com/article2</link>
    </item>
  </channel>
</rss>"""


class TestNewsService:
    def test_parse_entry_basic(self):
        import feedparser
        feed = feedparser.parse(SAMPLE_RSS)
        service = NewsService()

        article = service._parse_entry(feed.entries[0])

        assert article is not None
        assert article["title"] == "Test Article 1"
        assert article["link"] == "https://example.com/article1"
        assert article["description"] == "This is a test article"

    def test_parse_entry_minimal(self):
        import feedparser
        feed = feedparser.parse(SAMPLE_RSS)
        service = NewsService()

        article = service._parse_entry(feed.entries[1])

        assert article is not None
        assert article["title"] == "Test Article 2"
        assert article["description"] is None or article["description"] == ""

    def test_get_default_feeds(self):
        service = NewsService()
        defaults = service.get_default_feeds()

        assert "tech" in defaults
        assert "general" in defaults
        assert len(defaults["tech"]) > 0
        assert all("name" in f and "url" in f for f in defaults["tech"])
```

## Acceptance Criteria
- [ ] News articles display from RSS feeds
- [ ] Category filtering works
- [ ] Articles link to original source
- [ ] Time ago formatting (5m, 2h, 1d)
- [ ] Add custom RSS feed
- [ ] Add default feeds by category
- [ ] Remove news sources
- [ ] Auto-refresh with 15-minute cache
- [ ] Manual refresh button
- [ ] Max 20 sources per user
- [ ] Handles feed errors gracefully
- [ ] Unit tests pass

## Notes
- RSS feeds are free and widely available
- 15-minute cache prevents excessive requests
- Consider adding background job for periodic refresh
- Some feeds may require User-Agent header

## Estimated Time
2-3 hours

## Next Task
Task 016: Fitness Stats Widget
