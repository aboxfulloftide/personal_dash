"""CRUD operations for reminders."""
from datetime import date, datetime, time, timedelta
from typing import Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.reminder import Reminder, ReminderInstance
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderInstanceCreate,
    ReminderInstanceUpdate,
    TodayReminderDisplay,
)


# ===== Reminder CRUD Operations =====


def create_reminder(db: Session, user_id: int, reminder_data: ReminderCreate) -> Reminder:
    """Create a new reminder for a user."""
    reminder = Reminder(
        user_id=user_id,
        **reminder_data.model_dump()
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def get_reminder(db: Session, reminder_id: int, user_id: int) -> Optional[Reminder]:
    """Get a specific reminder by ID for a user."""
    stmt = select(Reminder).where(
        and_(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        )
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def get_user_reminders(
    db: Session,
    user_id: int,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100
) -> list[Reminder]:
    """Get all reminders for a user."""
    stmt = select(Reminder).where(Reminder.user_id == user_id)

    if active_only:
        stmt = stmt.where(Reminder.is_active == True)

    stmt = stmt.order_by(Reminder.created_at.desc()).offset(skip).limit(limit)
    result = db.execute(stmt)
    return list(result.scalars().all())


def update_reminder(
    db: Session,
    reminder_id: int,
    user_id: int,
    reminder_data: ReminderUpdate
) -> Optional[Reminder]:
    """Update a reminder."""
    reminder = get_reminder(db, reminder_id, user_id)
    if not reminder:
        return None

    update_data = reminder_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder_id: int, user_id: int) -> bool:
    """Delete a reminder and all its instances."""
    reminder = get_reminder(db, reminder_id, user_id)
    if not reminder:
        return False

    db.delete(reminder)
    db.commit()
    return True


# ===== Reminder Instance CRUD Operations =====


def create_reminder_instance(
    db: Session,
    user_id: int,
    instance_data: ReminderInstanceCreate
) -> ReminderInstance:
    """Create a new reminder instance."""
    instance = ReminderInstance(
        user_id=user_id,
        **instance_data.model_dump()
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def get_reminder_instance(
    db: Session,
    instance_id: int,
    user_id: int
) -> Optional[ReminderInstance]:
    """Get a specific reminder instance by ID."""
    stmt = select(ReminderInstance).where(
        and_(
            ReminderInstance.id == instance_id,
            ReminderInstance.user_id == user_id
        )
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def get_instances_for_date(
    db: Session,
    user_id: int,
    target_date: date,
    include_overdue: bool = True
) -> list[ReminderInstance]:
    """Get all reminder instances for a specific date."""
    stmt = select(ReminderInstance).where(
        and_(
            ReminderInstance.user_id == user_id,
            ReminderInstance.due_date == target_date
        )
    ).order_by(
        ReminderInstance.due_time.asc(),
        ReminderInstance.created_at.asc()
    )

    if include_overdue:
        # Also include overdue reminders from previous dates
        overdue_stmt = select(ReminderInstance).where(
            and_(
                ReminderInstance.user_id == user_id,
                ReminderInstance.due_date < target_date,
                ReminderInstance.status == "pending",
                ReminderInstance.is_overdue == True
            )
        ).order_by(
            ReminderInstance.due_date.asc(),
            ReminderInstance.due_time.asc()
        )

        # Combine both queries
        result_today = db.execute(stmt)
        result_overdue = db.execute(overdue_stmt)

        instances_today = list(result_today.scalars().all())
        instances_overdue = list(result_overdue.scalars().all())

        return instances_overdue + instances_today
    else:
        result = db.execute(stmt)
        return list(result.scalars().all())


def get_today_reminders_display(db: Session, user_id: int) -> list[TodayReminderDisplay]:
    """Get today's reminders formatted for widget display."""
    today = date.today()

    stmt = select(ReminderInstance, Reminder).join(
        Reminder, ReminderInstance.reminder_id == Reminder.id
    ).where(
        and_(
            ReminderInstance.user_id == user_id,
            ReminderInstance.status != "acknowledged",
            or_(
                ReminderInstance.due_date == today,
                and_(
                    ReminderInstance.due_date < today,
                    ReminderInstance.status == "pending",
                    Reminder.carry_over == True
                )
            )
        )
    ).order_by(
        ReminderInstance.is_overdue.asc(),  # Non-overdue first
        ReminderInstance.due_time.asc(),
        ReminderInstance.created_at.asc()
    )

    result = db.execute(stmt)
    rows = result.all()

    reminders_display = []
    for instance, reminder in rows:
        reminders_display.append(
            TodayReminderDisplay(
                instance_id=instance.id,
                reminder_id=instance.reminder_id,
                title=reminder.title,
                notes=reminder.notes,
                due_date=instance.due_date,
                due_time=instance.due_time,
                instance_number=instance.instance_number,
                status=instance.status,
                is_overdue=instance.is_overdue,
                dismissed_at=instance.dismissed_at,
            )
        )

    return reminders_display


def get_tripped_reminder_counts(db: Session, user_id: int) -> dict:
    """
    Count reminders that are currently "tripped" (due or overdue) and still
    pending/dismissed (not acknowledged).  Returns {"total": int, "overdue": int, "due": int}.
    """
    now = datetime.now()
    today = date.today()
    current_time = now.time()

    display = get_today_reminders_display(db, user_id)

    overdue = 0
    due = 0
    for r in display:
        if r.is_overdue:
            overdue += 1
        elif r.due_time is None or r.due_time <= current_time:
            # No specific time means due all day; otherwise due if time has passed
            due += 1
        # else: future reminder today — not tripped yet

    return {"total": overdue + due, "overdue": overdue, "due": due}


def dismiss_reminder_instance(
    db: Session,
    instance_id: int,
    user_id: int
) -> Optional[ReminderInstance]:
    """Dismiss a reminder instance."""
    instance = get_reminder_instance(db, instance_id, user_id)
    if not instance:
        return None

    instance.status = "dismissed"
    instance.dismissed_at = datetime.now()
    db.commit()
    db.refresh(instance)
    return instance


def acknowledge_reminder_instance(
    db: Session,
    instance_id: int,
    user_id: int
) -> Optional[ReminderInstance]:
    """Acknowledge a reminder instance (removes it from display)."""
    instance = get_reminder_instance(db, instance_id, user_id)
    if not instance:
        return None

    instance.status = "acknowledged"
    instance.dismissed_at = datetime.now()
    db.commit()
    db.refresh(instance)
    return instance


def update_reminder_instance(
    db: Session,
    instance_id: int,
    user_id: int,
    instance_data: ReminderInstanceUpdate
) -> Optional[ReminderInstance]:
    """Update a reminder instance."""
    instance = get_reminder_instance(db, instance_id, user_id)
    if not instance:
        return None

    update_data = instance_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(instance, field, value)

    db.commit()
    db.refresh(instance)
    return instance


def check_instance_exists(
    db: Session,
    reminder_id: int,
    due_date: date,
    due_time: Optional[time] = None,
    instance_number: Optional[int] = None
) -> bool:
    """Check if a reminder instance already exists for a specific date/time."""
    stmt = select(ReminderInstance).where(
        and_(
            ReminderInstance.reminder_id == reminder_id,
            ReminderInstance.due_date == due_date
        )
    )

    if due_time is not None:
        stmt = stmt.where(ReminderInstance.due_time == due_time)

    if instance_number is not None:
        stmt = stmt.where(ReminderInstance.instance_number == instance_number)

    result = db.execute(stmt)
    return result.scalar_one_or_none() is not None


# ===== Instance Generation =====


def generate_instances_for_reminder(db: Session, reminder: "Reminder") -> int:
    """
    Generate today's instances for a single reminder if applicable.
    Returns the number of instances created.
    """
    today = date.today()
    today_weekday = today.weekday()

    if not reminder.is_active or reminder.start_date > today:
        return 0

    instances_created = 0

    if reminder.recurrence_type == "day_of_week":
        if reminder.days_of_week:
            days = [int(d.strip()) for d in reminder.days_of_week.split(",")]
            if today_weekday in days:
                if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                    instance_data = ReminderInstanceCreate(
                        reminder_id=reminder.id,
                        due_date=today,
                        due_time=reminder.reminder_time,
                        status="pending",
                        is_overdue=False,
                    )
                    create_reminder_instance(db, reminder.user_id, instance_data)
                    instances_created += 1

    elif reminder.recurrence_type == "interval":
        if reminder.interval_unit == "hours":
            hours_per_day = 24
            interval = reminder.interval_value
            instances_per_day = hours_per_day // interval

            for i in range(instances_per_day):
                hour = i * interval
                due_time = time(hour=hour, minute=0, second=0)

                if not check_instance_exists(db, reminder.id, today, due_time, i + 1):
                    instance_data = ReminderInstanceCreate(
                        reminder_id=reminder.id,
                        due_date=today,
                        due_time=due_time,
                        instance_number=i + 1,
                        status="pending",
                        is_overdue=False,
                    )
                    create_reminder_instance(db, reminder.user_id, instance_data)
                    instances_created += 1

        elif reminder.interval_unit == "days":
            days_since_start = (today - reminder.start_date).days
            if days_since_start % reminder.interval_value == 0:
                if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                    instance_data = ReminderInstanceCreate(
                        reminder_id=reminder.id,
                        due_date=today,
                        due_time=reminder.reminder_time,
                        status="pending",
                        is_overdue=False,
                    )
                    create_reminder_instance(db, reminder.user_id, instance_data)
                    instances_created += 1

        elif reminder.interval_unit == "weeks":
            days_since_start = (today - reminder.start_date).days
            weeks_since_start = days_since_start // 7
            if weeks_since_start % reminder.interval_value == 0 and today.weekday() == reminder.start_date.weekday():
                if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                    instance_data = ReminderInstanceCreate(
                        reminder_id=reminder.id,
                        due_date=today,
                        due_time=reminder.reminder_time,
                        status="pending",
                        is_overdue=False,
                    )
                    create_reminder_instance(db, reminder.user_id, instance_data)
                    instances_created += 1

        elif reminder.interval_unit == "months":
            months_since_start = (today.year - reminder.start_date.year) * 12 + (today.month - reminder.start_date.month)
            if months_since_start % reminder.interval_value == 0 and today.day == reminder.start_date.day:
                if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                    instance_data = ReminderInstanceCreate(
                        reminder_id=reminder.id,
                        due_date=today,
                        due_time=reminder.reminder_time,
                        status="pending",
                        is_overdue=False,
                    )
                    create_reminder_instance(db, reminder.user_id, instance_data)
                    instances_created += 1

    return instances_created


# ===== Midnight Reset Operations =====


def mark_missed_reminders(db: Session) -> int:
    """
    Mark pending reminders from previous days as 'missed'.
    Only applies to reminders with carry_over=False.
    Returns count of marked reminders.
    """
    yesterday = date.today() - timedelta(days=1)

    # Find reminders with carry_over=False
    stmt = select(ReminderInstance, Reminder).join(
        Reminder, ReminderInstance.reminder_id == Reminder.id
    ).where(
        and_(
            ReminderInstance.due_date < date.today(),
            ReminderInstance.status.in_(["pending", "dismissed"]),
            Reminder.carry_over == False
        )
    )

    result = db.execute(stmt)
    instances_to_mark = [inst for inst, rem in result.all()]

    count = 0
    for instance in instances_to_mark:
        instance.status = "missed"
        count += 1

    if count > 0:
        db.commit()

    return count


def mark_overdue_reminders(db: Session) -> int:
    """
    Mark pending reminders from previous days as overdue.
    Only applies to reminders with carry_over=True.
    Returns count of marked reminders.
    """
    stmt = select(ReminderInstance, Reminder).join(
        Reminder, ReminderInstance.reminder_id == Reminder.id
    ).where(
        and_(
            ReminderInstance.due_date < date.today(),
            ReminderInstance.status.in_(["pending", "dismissed"]),
            ReminderInstance.is_overdue == False,
            Reminder.carry_over == True
        )
    )

    result = db.execute(stmt)
    instances_to_mark = [inst for inst, rem in result.all()]

    count = 0
    for instance in instances_to_mark:
        instance.is_overdue = True
        count += 1

    if count > 0:
        db.commit()

    return count
