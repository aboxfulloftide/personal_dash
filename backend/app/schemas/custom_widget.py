from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CustomWidgetItemCreate(BaseModel):
    title: str
    subtitle: str | None = None
    description: str | None = None
    icon: str | None = None
    link_url: str | None = None
    link_text: str | None = None
    visible: bool = True
    alert_active: bool = False
    alert_severity: str | None = None
    alert_message: str | None = None
    highlight: bool = False
    color: str | None = None
    priority: int = 0


class CustomWidgetItemUpdate(CustomWidgetItemCreate):
    pass


class CustomWidgetItemResponse(CustomWidgetItemCreate):
    id: int
    user_id: int
    widget_id: str
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CustomWidgetResponse(BaseModel):
    items: list[CustomWidgetItemResponse]
    total_count: int
    alert_active: bool
    alert_severity: str | None
    alert_message: str | None


class BulkCreateRequest(BaseModel):
    items: list[CustomWidgetItemCreate]
    replace_all: bool = False
