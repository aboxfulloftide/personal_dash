from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timezone

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.schemas.widget import (
    DashboardData,
    WidgetItem,
    WidgetConfigUpdate,
    WidgetTypesResponse,
)
from app.crud.dashboard import (
    get_dashboard,
    save_dashboard,
    get_widget_from_dashboard,
    update_widget_config,
    delete_widget_from_dashboard,
)
from app.core.widget_registry import get_widget_types, is_valid_widget_type

router = APIRouter(tags=["Dashboard"])


# --- Widget Types ---

@router.get("/widgets/types", response_model=WidgetTypesResponse)
def list_widget_types(current_user: CurrentActiveUser):
    """List all available widget types and their config schemas."""
    return WidgetTypesResponse(widget_types=get_widget_types())


# --- Dashboard Layout ---

@router.get("/dashboard/layout", response_model=DashboardData)
def get_dashboard_layout(current_user: CurrentActiveUser, db: DbSession):
    """Get user's dashboard layout and widgets."""
    dashboard = get_dashboard(db, current_user.id)
    if not dashboard:
        return DashboardData(widgets=[], layout=[])

    return DashboardData(
        widgets=dashboard.layout.get("widgets", []),
        layout=dashboard.layout.get("layout", []),
    )


@router.put("/dashboard/layout", response_model=DashboardData)
def save_dashboard_layout(
    data: DashboardData, current_user: CurrentActiveUser, db: DbSession
):
    """Save user's dashboard layout and widgets."""
    layout_data = {
        "widgets": [w.model_dump() for w in data.widgets],
        "layout": [l.model_dump() for l in data.layout],
    }
    save_dashboard(db, current_user.id, layout_data)
    return data


# --- Individual Widget Operations ---

@router.get("/widgets/{widget_id}", response_model=WidgetItem)
def get_widget(
    widget_id: str, current_user: CurrentActiveUser, db: DbSession
):
    """Get a single widget's configuration."""
    widget = get_widget_from_dashboard(db, current_user.id, widget_id)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )
    return widget


@router.patch("/widgets/{widget_id}/config", response_model=WidgetItem)
def patch_widget_config(
    widget_id: str,
    data: WidgetConfigUpdate,
    current_user: CurrentActiveUser,
    db: DbSession,
):
    """Update a single widget's configuration."""
    widget = update_widget_config(db, current_user.id, widget_id, data.config)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )
    return widget


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_widget(
    widget_id: str, current_user: CurrentActiveUser, db: DbSession
):
    """Remove a widget from the dashboard."""
    deleted = delete_widget_from_dashboard(db, current_user.id, widget_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )


# --- Alert System ---

class AlertRequest(BaseModel):
    severity: str  # 'critical', 'warning', 'info'
    message: str
    auto_dismiss_seconds: int | None = None


class AlertResponse(BaseModel):
    success: bool
    widget_id: str
    alert_active: bool
    severity: str | None = None
    message: str | None = None


@router.post("/widgets/{widget_id}/alert", response_model=AlertResponse)
def trigger_widget_alert(
    widget_id: str,
    alert_data: AlertRequest,
    current_user: CurrentActiveUser,
    db: DbSession,
):
    """
    Trigger an alert on a widget.
    The widget will move to the top of the dashboard until acknowledged.
    """
    # Get the widget
    widget = get_widget_from_dashboard(db, current_user.id, widget_id)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )

    # Validate severity
    valid_severities = ['critical', 'warning', 'info']
    if alert_data.severity not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity. Must be one of: {', '.join(valid_severities)}"
        )

    # Update widget with alert info via CRUD
    from app.crud.dashboard import trigger_widget_alert as crud_trigger_alert
    updated_widget = crud_trigger_alert(
        db,
        current_user.id,
        widget_id,
        alert_data.severity,
        alert_data.message
    )

    return AlertResponse(
        success=True,
        widget_id=widget_id,
        alert_active=True,
        severity=alert_data.severity,
        message=alert_data.message,
    )


@router.post("/widgets/{widget_id}/acknowledge", response_model=AlertResponse)
def acknowledge_widget_alert(
    widget_id: str,
    current_user: CurrentActiveUser,
    db: DbSession,
):
    """
    Acknowledge and clear an alert on a widget.
    The widget will return to its original position.
    """
    # Get the widget
    widget = get_widget_from_dashboard(db, current_user.id, widget_id)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )

    # Clear alert via CRUD
    from app.crud.dashboard import acknowledge_widget_alert as crud_acknowledge_alert
    updated_widget = crud_acknowledge_alert(db, current_user.id, widget_id)

    # If this is a custom widget, also acknowledge item-level alerts so the scheduler
    # doesn't immediately re-trigger the alert on its next run.
    if widget.get("type") == "custom_widget":
        from app.crud.custom_widget import acknowledge_widget_items
        acknowledge_widget_items(db, current_user.id, widget_id)

    return AlertResponse(
        success=True,
        widget_id=widget_id,
        alert_active=False,
        severity=None,
        message=None,
    )
