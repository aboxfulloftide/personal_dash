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
