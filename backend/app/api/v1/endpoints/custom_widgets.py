from fastapi import APIRouter, HTTPException

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.schemas.custom_widget import (
    BulkCreateRequest,
    CustomWidgetItemCreate,
    CustomWidgetItemResponse,
    CustomWidgetItemUpdate,
    CustomWidgetResponse,
)
import app.crud.custom_widget as crud

router = APIRouter(prefix="/custom-widgets", tags=["Custom Widgets"])


@router.get("/{widget_id}/items", response_model=CustomWidgetResponse)
def get_items(
    widget_id: str,
    max_items: int = 50,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Get visible items for a widget (for display)."""
    items = crud.get_items(db, current_user.id, widget_id, visible_only=True, limit=max_items)
    alert_active, alert_severity, alert_message = crud.get_alert_status(db, current_user.id, widget_id)
    return CustomWidgetResponse(
        items=items,
        total_count=len(items),
        alert_active=alert_active,
        alert_severity=alert_severity,
        alert_message=alert_message,
    )


@router.get("/{widget_id}/items/all", response_model=list[CustomWidgetItemResponse])
def get_all_items(
    widget_id: str,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Get all items including hidden (for manage UI)."""
    return crud.get_all_items(db, current_user.id, widget_id)


@router.post("/{widget_id}/items", response_model=CustomWidgetItemResponse, status_code=201)
def create_item(
    widget_id: str,
    data: CustomWidgetItemCreate,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Create a new item."""
    return crud.create_item(db, current_user.id, widget_id, data)


@router.put("/{widget_id}/items/{item_id}", response_model=CustomWidgetItemResponse)
def update_item(
    widget_id: str,
    item_id: int,
    data: CustomWidgetItemUpdate,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Update an existing item."""
    item = crud.update_item(db, current_user.id, item_id, data)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{widget_id}/items/{item_id}", status_code=204)
def delete_item(
    widget_id: str,
    item_id: int,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Delete a single item."""
    deleted = crud.delete_item(db, current_user.id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/{widget_id}/items", status_code=204)
def delete_all_items(
    widget_id: str,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Delete all items for a widget (called on widget removal)."""
    crud.delete_all_items(db, current_user.id, widget_id)


@router.post("/{widget_id}/items/bulk", response_model=list[CustomWidgetItemResponse], status_code=201)
def bulk_create_items(
    widget_id: str,
    data: BulkCreateRequest,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """
    Create multiple items at once. If replace_all=true, deletes all existing items first.
    Useful for scripts that push a full state snapshot.
    """
    if not data.items:
        raise HTTPException(status_code=422, detail="items list cannot be empty")
    return crud.bulk_create_items(db, current_user.id, widget_id, data.items, data.replace_all)


@router.post("/{widget_id}/items/{item_id}/acknowledge", response_model=CustomWidgetItemResponse)
def acknowledge_item(
    widget_id: str,
    item_id: int,
    db: DbSession = None,
    current_user: CurrentActiveUser = None,
):
    """Acknowledge a single item's alert (suppresses widget-level alert until re-triggered)."""
    item = crud.acknowledge_item(db, current_user.id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
