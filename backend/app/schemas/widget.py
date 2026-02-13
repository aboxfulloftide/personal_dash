from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class WidgetCategory(str, Enum):
    MONITORING = "monitoring"
    FINANCE = "finance"
    LIFESTYLE = "lifestyle"
    PRODUCTIVITY = "productivity"
    OTHER = "other"


class ConfigFieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    TOGGLE = "toggle"


class ConfigField(BaseModel):
    """Schema for a single widget configuration field."""
    type: ConfigFieldType
    label: str
    default: Any = None
    required: bool = False
    placeholder: str = ""
    # For number fields
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    # For select fields
    options: Optional[list[dict[str, str]]] = None


class WidgetSize(BaseModel):
    w: int
    h: int


class WidgetTypeInfo(BaseModel):
    """Metadata for a widget type returned by the API."""
    type: str
    name: str
    description: str
    category: WidgetCategory
    default_size: WidgetSize
    min_size: WidgetSize
    max_size: WidgetSize
    config_schema: dict[str, ConfigField] = {}
    has_data_endpoint: bool = False


class WidgetTypesResponse(BaseModel):
    widget_types: list[WidgetTypeInfo]


# --- Dashboard layout schemas (moved from endpoint inline) ---

class LayoutItem(BaseModel):
    i: str
    x: int
    y: int
    w: int
    h: int
    minW: Optional[int] = None
    minH: Optional[int] = None
    maxW: Optional[int] = None
    maxH: Optional[int] = None


class WidgetItem(BaseModel):
    id: str
    type: str
    config: dict = {}
    # Alert system fields
    alert_active: Optional[bool] = False
    alert_severity: Optional[str] = None
    alert_message: Optional[str] = None
    alert_triggered_at: Optional[str] = None
    original_layout_x: Optional[int] = None
    original_layout_y: Optional[int] = None


class DashboardData(BaseModel):
    widgets: list[WidgetItem]
    layout: list[LayoutItem]


class WidgetConfigUpdate(BaseModel):
    """Update config for a single widget."""
    config: dict = Field(..., description="Widget configuration key-value pairs")
