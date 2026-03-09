from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timezone

from app.models.widget import DashboardLayout


def get_dashboard(db: Session, user_id: int) -> DashboardLayout | None:
    """Get a user's dashboard layout."""
    stmt = select(DashboardLayout).where(DashboardLayout.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def save_dashboard(db: Session, user_id: int, layout_data: dict) -> DashboardLayout:
    """Create or update a user's dashboard layout."""
    dashboard = get_dashboard(db, user_id)
    if dashboard:
        dashboard.layout = layout_data
        flag_modified(dashboard, "layout")
        db.commit()
        db.refresh(dashboard)
        return dashboard

    # Try to insert new record
    try:
        dashboard = DashboardLayout(user_id=user_id, layout=layout_data)
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        return dashboard
    except IntegrityError:
        # Race condition: another request created the record first
        db.rollback()
        dashboard = get_dashboard(db, user_id)
        if dashboard:
            dashboard.layout = layout_data
            flag_modified(dashboard, "layout")
            db.commit()
            db.refresh(dashboard)
            return dashboard
        raise


def get_widget_from_dashboard(
    db: Session, user_id: int, widget_id: str
) -> dict | None:
    """Get a single widget's data from the dashboard layout."""
    dashboard = get_dashboard(db, user_id)
    if not dashboard or not dashboard.layout:
        return None
    widgets = dashboard.layout.get("widgets", [])
    for widget in widgets:
        if widget.get("id") == widget_id:
            return widget
    return None


def update_widget_config(
    db: Session, user_id: int, widget_id: str, config: dict
) -> dict | None:
    """Update a single widget's config within the dashboard layout."""
    dashboard = get_dashboard(db, user_id)
    if not dashboard or not dashboard.layout:
        return None

    widgets = dashboard.layout.get("widgets", [])
    updated_widget = None
    for widget in widgets:
        if widget.get("id") == widget_id:
            widget["config"] = {**widget.get("config", {}), **config}
            updated_widget = widget
            break

    if updated_widget is None:
        return None

    # SQLAlchemy needs reassignment to detect JSON mutation
    dashboard.layout = {**dashboard.layout, "widgets": widgets}
    flag_modified(dashboard, "layout")
    db.commit()
    db.refresh(dashboard)
    return updated_widget


def delete_widget_from_dashboard(
    db: Session, user_id: int, widget_id: str
) -> bool:
    """Remove a widget from the dashboard."""
    dashboard = get_dashboard(db, user_id)
    if not dashboard or not dashboard.layout:
        return False

    widgets = dashboard.layout.get("widgets", [])
    layout_items = dashboard.layout.get("layout", [])

    new_widgets = [w for w in widgets if w.get("id") != widget_id]
    new_layout = [l for l in layout_items if l.get("i") != widget_id]

    if len(new_widgets) == len(widgets):
        return False

    dashboard.layout = {"widgets": new_widgets, "layout": new_layout}
    flag_modified(dashboard, "layout")
    db.commit()
    return True


def trigger_widget_alert(
    db: Session,
    user_id: int,
    widget_id: str,
    severity: str,
    message: str
) -> dict | None:
    """Trigger an alert on a widget. Stores current position for later restoration."""
    dashboard = get_dashboard(db, user_id)
    if not dashboard or not dashboard.layout:
        return None

    widgets = dashboard.layout.get("widgets", [])
    layout_items = dashboard.layout.get("layout", [])

    updated_widget = None
    for widget in widgets:
        if widget.get("id") == widget_id:
            # Find current layout position
            current_layout = None
            for layout_item in layout_items:
                if layout_item.get("i") == widget_id:
                    current_layout = layout_item
                    break

            # Store original position
            if current_layout:
                widget["original_layout_x"] = current_layout.get("x")
                widget["original_layout_y"] = current_layout.get("y")

            # Set alert fields
            widget["alert_active"] = True
            widget["alert_severity"] = severity
            widget["alert_message"] = message
            widget["alert_triggered_at"] = datetime.now(timezone.utc).isoformat()
            widget["alert_acknowledged_message"] = None  # Clear acked state

            updated_widget = widget
            break

    if updated_widget is None:
        return None

    # SQLAlchemy needs reassignment to detect JSON mutation
    dashboard.layout = {**dashboard.layout, "widgets": widgets}
    flag_modified(dashboard, "layout")  # Explicitly mark JSON column as modified
    db.commit()
    db.refresh(dashboard)
    return updated_widget


def acknowledge_widget_alert(
    db: Session,
    user_id: int,
    widget_id: str
) -> dict | None:
    """Acknowledge and clear a widget alert."""
    dashboard = get_dashboard(db, user_id)
    if not dashboard or not dashboard.layout:
        return None

    widgets = dashboard.layout.get("widgets", [])

    updated_widget = None
    for widget in widgets:
        if widget.get("id") == widget_id:
            # Remember what was acknowledged so the monitor won't re-trigger
            # the same alert until the situation changes
            widget["alert_acknowledged_message"] = widget.get("alert_message")
            # Clear alert fields
            widget["alert_active"] = False
            widget["alert_severity"] = None
            widget["alert_message"] = None
            widget["alert_triggered_at"] = None
            widget["original_layout_x"] = None
            widget["original_layout_y"] = None

            updated_widget = widget
            break

    if updated_widget is None:
        return None

    # SQLAlchemy needs reassignment to detect JSON mutation
    dashboard.layout = {**dashboard.layout, "widgets": widgets}
    flag_modified(dashboard, "layout")
    db.commit()
    db.refresh(dashboard)
    return updated_widget
