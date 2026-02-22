from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models.custom_widget import CustomWidgetData
from app.schemas.custom_widget import CustomWidgetItemCreate, CustomWidgetItemUpdate


def get_items(
    db: Session,
    user_id: int,
    widget_id: str,
    visible_only: bool = True,
    limit: int = 50,
) -> list[CustomWidgetData]:
    """Get items for a widget, sorted by priority desc, created_at asc."""
    stmt = select(CustomWidgetData).where(
        CustomWidgetData.user_id == user_id,
        CustomWidgetData.widget_id == widget_id,
    )
    if visible_only:
        stmt = stmt.where(CustomWidgetData.visible == True)
    stmt = stmt.order_by(
        CustomWidgetData.priority.desc(),
        CustomWidgetData.created_at.asc(),
    ).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_all_items(db: Session, user_id: int, widget_id: str) -> list[CustomWidgetData]:
    """Get all items including hidden, for the manage UI."""
    stmt = (
        select(CustomWidgetData)
        .where(
            CustomWidgetData.user_id == user_id,
            CustomWidgetData.widget_id == widget_id,
        )
        .order_by(
            CustomWidgetData.priority.desc(),
            CustomWidgetData.created_at.asc(),
        )
    )
    return list(db.execute(stmt).scalars().all())


def create_item(
    db: Session,
    user_id: int,
    widget_id: str,
    data: CustomWidgetItemCreate,
) -> CustomWidgetData:
    """Create a new item."""
    item = CustomWidgetData(
        user_id=user_id,
        widget_id=widget_id,
        **data.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session,
    user_id: int,
    item_id: int,
    data: CustomWidgetItemUpdate,
) -> CustomWidgetData | None:
    """Update an existing item."""
    stmt = select(CustomWidgetData).where(
        CustomWidgetData.id == item_id,
        CustomWidgetData.user_id == user_id,
    )
    item = db.execute(stmt).scalar_one_or_none()
    if item is None:
        return None
    for field, value in data.model_dump().items():
        setattr(item, field, value)
    # Reset acknowledged if the alert is being re-activated
    if data.alert_active:
        item.acknowledged = False
        item.acknowledged_at = None
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, user_id: int, item_id: int) -> bool:
    """Delete a single item."""
    stmt = select(CustomWidgetData).where(
        CustomWidgetData.id == item_id,
        CustomWidgetData.user_id == user_id,
    )
    item = db.execute(stmt).scalar_one_or_none()
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def delete_all_items(db: Session, user_id: int, widget_id: str) -> int:
    """Delete all items for a widget. Returns count deleted."""
    stmt = delete(CustomWidgetData).where(
        CustomWidgetData.user_id == user_id,
        CustomWidgetData.widget_id == widget_id,
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def bulk_create_items(
    db: Session,
    user_id: int,
    widget_id: str,
    items_data: list,
    replace_all: bool = False,
) -> list[CustomWidgetData]:
    """Create multiple items at once, optionally replacing all existing items first."""
    if replace_all:
        stmt = delete(CustomWidgetData).where(
            CustomWidgetData.user_id == user_id,
            CustomWidgetData.widget_id == widget_id,
        )
        db.execute(stmt)

    new_items = [
        CustomWidgetData(user_id=user_id, widget_id=widget_id, **data.model_dump())
        for data in items_data
    ]
    db.add_all(new_items)
    db.commit()
    for item in new_items:
        db.refresh(item)
    return new_items


def acknowledge_item(db: Session, user_id: int, item_id: int) -> CustomWidgetData | None:
    """Acknowledge a single item's alert."""
    stmt = select(CustomWidgetData).where(
        CustomWidgetData.id == item_id,
        CustomWidgetData.user_id == user_id,
    )
    item = db.execute(stmt).scalar_one_or_none()
    if item is None:
        return None
    item.acknowledged = True
    item.acknowledged_at = datetime.now()
    db.commit()
    db.refresh(item)
    return item


def acknowledge_widget_items(db: Session, user_id: int, widget_id: str) -> int:
    """Acknowledge all active alert items for a widget. Returns count acknowledged."""
    stmt = select(CustomWidgetData).where(
        CustomWidgetData.user_id == user_id,
        CustomWidgetData.widget_id == widget_id,
        CustomWidgetData.alert_active == True,
        CustomWidgetData.acknowledged == False,
    )
    items = list(db.execute(stmt).scalars().all())
    now = datetime.now()
    for item in items:
        item.acknowledged = True
        item.acknowledged_at = now
    db.commit()
    return len(items)


def get_alert_status(
    db: Session, user_id: int, widget_id: str
) -> tuple[bool, str | None, str | None]:
    """
    Return (alert_active, alert_severity, alert_message) for a widget.
    Checks if any visible item has alert_active=True and acknowledged=False.
    Severity precedence: critical > warning > info.
    """
    items = get_items(db, user_id, widget_id, visible_only=True)
    alert_items = [i for i in items if i.alert_active and not i.acknowledged]
    if not alert_items:
        return False, None, None

    severity_order = {"critical": 3, "warning": 2, "info": 1}
    highest = max(alert_items, key=lambda i: severity_order.get(i.alert_severity or "info", 0))

    # Build message from first alerting item (or count if multiple)
    if len(alert_items) == 1:
        message = highest.alert_message or highest.title
    else:
        message = f"{len(alert_items)} items need attention"

    return True, highest.alert_severity or "info", message
