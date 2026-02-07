"""
Backend widget type registry.

Defines all available widget types, their metadata, and configuration schemas.
New widgets are added by creating an entry here.
"""

from app.schemas.widget import (
    WidgetTypeInfo,
    WidgetSize,
    WidgetCategory,
    ConfigField,
    ConfigFieldType,
)

# Common config fields reused across widgets
REFRESH_INTERVAL_FIELD = ConfigField(
    type=ConfigFieldType.NUMBER,
    label="Refresh Interval (seconds)",
    default=300,
    min=30,
    max=3600,
    step=30,
)

TITLE_FIELD = ConfigField(
    type=ConfigFieldType.TEXT,
    label="Title",
    default="",
    placeholder="Widget title",
)

# --- Widget type definitions ---

WIDGET_TYPES: dict[str, WidgetTypeInfo] = {
    "server_monitor": WidgetTypeInfo(
        type="server_monitor",
        name="Server Monitor",
        description="Monitor server CPU, memory, disk, and Docker containers",
        category=WidgetCategory.MONITORING,
        default_size=WidgetSize(w=3, h=3),
        min_size=WidgetSize(w=2, h=2),
        max_size=WidgetSize(w=6, h=6),
        has_data_endpoint=True,
        config_schema={
            "title": TITLE_FIELD,
            "server_id": ConfigField(
                type=ConfigFieldType.NUMBER,
                label="Server ID",
                required=True,
            ),
            "refresh_interval": REFRESH_INTERVAL_FIELD,
            "show_docker": ConfigField(
                type=ConfigFieldType.TOGGLE,
                label="Show Docker Containers",
                default=True,
            ),
        },
    ),
    "package_tracker": WidgetTypeInfo(
        type="package_tracker",
        name="Package Tracker",
        description="Track packages from USPS, UPS, FedEx, and Amazon",
        category=WidgetCategory.LIFESTYLE,
        default_size=WidgetSize(w=3, h=3),
        min_size=WidgetSize(w=2, h=2),
        max_size=WidgetSize(w=6, h=6),
        has_data_endpoint=True,
        config_schema={
            "title": TITLE_FIELD,
            "show_delivered": ConfigField(
                type=ConfigFieldType.TOGGLE,
                label="Show Delivered Packages",
                default=False,
            ),
            "refresh_interval": REFRESH_INTERVAL_FIELD,
        },
    ),
    "stock_ticker": WidgetTypeInfo(
        type="stock_ticker",
        name="Stock Ticker",
        description="Real-time stock price tracking",
        category=WidgetCategory.FINANCE,
        default_size=WidgetSize(w=2, h=2),
        min_size=WidgetSize(w=2, h=1),
        max_size=WidgetSize(w=6, h=4),
        has_data_endpoint=True,
        config_schema={
            "title": TITLE_FIELD,
            "symbols": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Stock Symbols (comma-separated)",
                default="AAPL,GOOGL,MSFT",
                placeholder="AAPL,GOOGL,MSFT",
            ),
            "refresh_interval": REFRESH_INTERVAL_FIELD,
        },
    ),
    "crypto_prices": WidgetTypeInfo(
        type="crypto_prices",
        name="Crypto Prices",
        description="Cryptocurrency price tracking",
        category=WidgetCategory.FINANCE,
        default_size=WidgetSize(w=2, h=2),
        min_size=WidgetSize(w=2, h=1),
        max_size=WidgetSize(w=6, h=4),
        has_data_endpoint=True,
        config_schema={
            "title": TITLE_FIELD,
            "coins": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Coins (comma-separated)",
                default="bitcoin,ethereum",
                placeholder="bitcoin,ethereum,solana",
            ),
            "currency": ConfigField(
                type=ConfigFieldType.SELECT,
                label="Display Currency",
                default="usd",
                options=[
                    {"value": "usd", "label": "USD"},
                    {"value": "eur", "label": "EUR"},
                    {"value": "gbp", "label": "GBP"},
                ],
            ),
            "refresh_interval": REFRESH_INTERVAL_FIELD,
        },
    ),
    "weather": WidgetTypeInfo(
        type="weather",
        name="Weather",
        description="Current weather conditions and forecast",
        category=WidgetCategory.LIFESTYLE,
        default_size=WidgetSize(w=2, h=2),
        min_size=WidgetSize(w=2, h=2),
        max_size=WidgetSize(w=4, h=4),
        has_data_endpoint=True,
        config_schema={
            "title": TITLE_FIELD,
            "location": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Location",
                default="",
                placeholder="City name or zip code",
                required=True,
            ),
            "units": ConfigField(
                type=ConfigFieldType.SELECT,
                label="Units",
                default="imperial",
                options=[
                    {"value": "imperial", "label": "Fahrenheit"},
                    {"value": "metric", "label": "Celsius"},
                ],
            ),
            "refresh_interval": REFRESH_INTERVAL_FIELD,
        },
    ),
    "fitness": WidgetTypeInfo(
        type="fitness",
        name="Fitness Stats",
        description="Body weight tracking with charts",
        category=WidgetCategory.LIFESTYLE,
        default_size=WidgetSize(w=3, h=2),
        min_size=WidgetSize(w=2, h=2),
        max_size=WidgetSize(w=6, h=4),
        has_data_endpoint=True,
        config_schema={
            "title": TITLE_FIELD,
            "days": ConfigField(
                type=ConfigFieldType.NUMBER,
                label="Days to Show",
                default=30,
                min=7,
                max=365,
                step=1,
            ),
            "goal_weight": ConfigField(
                type=ConfigFieldType.NUMBER,
                label="Goal Weight",
                default=None,
                min=50,
                max=500,
                step=0.1,
            ),
        },
    ),
    "news_headlines": WidgetTypeInfo(
        type="news_headlines",
        name="News Headlines",
        description="Aggregated RSS news feeds with optional NewsAPI.org support",
        category=WidgetCategory.LIFESTYLE,
        default_size=WidgetSize(w=3, h=3),
        min_size=WidgetSize(w=2, h=2),
        max_size=WidgetSize(w=6, h=6),
        has_data_endpoint=True,
        config_schema={
            "title": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Title",
                default="News Headlines",
                placeholder="Widget title",
            ),
            "provider": ConfigField(
                type=ConfigFieldType.SELECT,
                label="Provider",
                default="rss",
                options=[
                    {"value": "rss", "label": "RSS Feed"},
                    {"value": "newsapi", "label": "NewsAPI.org"},
                ],
            ),
            "source": ConfigField(
                type=ConfigFieldType.TEXT,
                label="News Sources (comma-separated)",
                default="bbc,techcrunch",
                placeholder="bbc,techcrunch,npr (available: bbc,npr,reuters,cnn,techcrunch,hackernews,custom)",
            ),
            "custom_url": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Custom RSS URL",
                default="",
                placeholder="https://example.com/feed.xml",
            ),
            "api_key": ConfigField(
                type=ConfigFieldType.TEXT,
                label="NewsAPI.org Key (optional)",
                default="",
                placeholder="Your NewsAPI.org API key",
            ),
            "category": ConfigField(
                type=ConfigFieldType.SELECT,
                label="NewsAPI Category",
                default="general",
                options=[
                    {"value": "general", "label": "General"},
                    {"value": "business", "label": "Business"},
                    {"value": "technology", "label": "Technology"},
                    {"value": "sports", "label": "Sports"},
                    {"value": "entertainment", "label": "Entertainment"},
                    {"value": "science", "label": "Science"},
                    {"value": "health", "label": "Health"},
                ],
            ),
            "max_articles": ConfigField(
                type=ConfigFieldType.NUMBER,
                label="Max Articles",
                default=10,
                min=5,
                max=50,
                step=5,
            ),
            "include_keywords": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Include Keywords (comma-separated)",
                default="",
                placeholder="tech, AI, startup (only show articles with these words)",
            ),
            "exclude_keywords": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Exclude Keywords (comma-separated)",
                default="",
                placeholder="apple, politics (hide articles with these words)",
            ),
            "refresh_interval": ConfigField(
                type=ConfigFieldType.NUMBER,
                label="Refresh Interval (seconds)",
                default=600,
                min=300,
                max=3600,
                step=60,
            ),
        },
    ),
    "calendar": WidgetTypeInfo(
        type="calendar",
        name="Calendar",
        description="Display events from ICS/iCal calendars with multiple views",
        category=WidgetCategory.LIFESTYLE,
        default_size=WidgetSize(w=3, h=3),
        min_size=WidgetSize(w=2, h=2),
        max_size=WidgetSize(w=6, h=6),
        has_data_endpoint=True,
        config_schema={
            "title": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Title",
                default="Calendar",
                placeholder="Widget title",
            ),
            "calendars": ConfigField(
                type=ConfigFieldType.TEXT,
                label="Calendar URLs (comma-separated ICS/iCal URLs)",
                default="",
                placeholder="https://calendar.google.com/calendar/ical/...",
                required=True,
            ),
            "default_view": ConfigField(
                type=ConfigFieldType.SELECT,
                label="Default View",
                default="week",
                options=[
                    {"value": "today", "label": "Today"},
                    {"value": "week", "label": "This Week"},
                    {"value": "month", "label": "Month"},
                ],
            ),
            "refresh_interval": ConfigField(
                type=ConfigFieldType.NUMBER,
                label="Refresh Interval (seconds)",
                default=600,
                min=300,
                max=3600,
                step=60,
            ),
        },
    ),
}


def get_widget_types() -> list[WidgetTypeInfo]:
    """Return all registered widget types."""
    return list(WIDGET_TYPES.values())


def get_widget_type(widget_type: str) -> WidgetTypeInfo | None:
    """Return a specific widget type definition, or None if not found."""
    return WIDGET_TYPES.get(widget_type)


def is_valid_widget_type(widget_type: str) -> bool:
    """Check if a widget type is registered."""
    return widget_type in WIDGET_TYPES
