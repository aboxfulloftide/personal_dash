"""API endpoints for reminders."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, get_db
from app.crud import reminder as crud
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderInstanceCreate,
    ReminderInstanceUpdate,
    ReminderInstanceResponse,
    RemindersWidgetResponse,
    TodayReminderDisplay,
)


router = APIRouter(prefix="/reminders", tags=["Reminders"])


# ===== Reminder Configuration Endpoints =====


@router.post("/", response_model=ReminderResponse, status_code=201)
def create_reminder(
    reminder_data: ReminderCreate,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Create a new recurring reminder."""
    reminder = crud.create_reminder(db, current_user.id, reminder_data)
    return reminder


@router.get("/", response_model=list[ReminderResponse])
def list_reminders(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Only return active reminders"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Get all reminders for the current user."""
    reminders = crud.get_user_reminders(
        db,
        current_user.id,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    return reminders


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: int,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Get a specific reminder by ID."""
    reminder = crud.get_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Update a reminder."""
    reminder = crud.update_reminder(db, reminder_id, current_user.id, reminder_data)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: int,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Delete a reminder and all its instances."""
    success = crud.delete_reminder(db, reminder_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return None


# ===== Reminder Instance Endpoints =====


@router.get("/instances/today", response_model=RemindersWidgetResponse)
def get_today_reminders(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """
    Get today's reminders for widget display.
    Includes overdue reminders from previous days if carry_over=True.
    """
    reminders = crud.get_today_reminders_display(db, current_user.id)

    total_count = len(reminders)
    pending_count = sum(1 for r in reminders if r.status == "pending")
    overdue_count = sum(1 for r in reminders if r.is_overdue and r.status == "pending")

    return RemindersWidgetResponse(
        reminders=reminders,
        total_count=total_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
    )


@router.post("/instances/{instance_id}/dismiss", response_model=ReminderInstanceResponse)
def dismiss_reminder(
    instance_id: int,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Dismiss a reminder instance."""
    instance = crud.dismiss_reminder_instance(db, instance_id, current_user.id)
    if not instance:
        raise HTTPException(status_code=404, detail="Reminder instance not found")

    # Convert to response model with reminder title
    from app.models.reminder import Reminder
    reminder = db.query(Reminder).filter(Reminder.id == instance.reminder_id).first()

    return ReminderInstanceResponse(
        id=instance.id,
        reminder_id=instance.reminder_id,
        user_id=instance.user_id,
        due_date=instance.due_date,
        due_time=instance.due_time,
        instance_number=instance.instance_number,
        status=instance.status,
        dismissed_at=instance.dismissed_at,
        is_overdue=instance.is_overdue,
        created_at=instance.created_at,
        reminder_title=reminder.title if reminder else None,
        reminder_notes=reminder.notes if reminder else None,
    )


@router.post("/instances/", response_model=ReminderInstanceResponse, status_code=201)
def create_reminder_instance(
    instance_data: ReminderInstanceCreate,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """
    Create a new reminder instance manually.
    Primarily used by background jobs for generating instances.
    """
    # Verify the reminder belongs to the user
    reminder = crud.get_reminder(db, instance_data.reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    # Check if instance already exists
    exists = crud.check_instance_exists(
        db,
        instance_data.reminder_id,
        instance_data.due_date,
        instance_data.due_time,
        instance_data.instance_number
    )
    if exists:
        raise HTTPException(status_code=409, detail="Instance already exists for this date/time")

    instance = crud.create_reminder_instance(db, current_user.id, instance_data)

    return ReminderInstanceResponse(
        id=instance.id,
        reminder_id=instance.reminder_id,
        user_id=instance.user_id,
        due_date=instance.due_date,
        due_time=instance.due_time,
        instance_number=instance.instance_number,
        status=instance.status,
        dismissed_at=instance.dismissed_at,
        is_overdue=instance.is_overdue,
        created_at=instance.created_at,
        reminder_title=reminder.title,
        reminder_notes=reminder.notes,
    )
