from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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
    db.commit()
    return True
