"""CRUD operations for fitness tracking."""
import json
import logging
import os
import tempfile
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session

from app.models.fitness import WeightEntry, GarminCredential, GarminDailyStat, GarminActivity
from app.schemas.fitness import WeightEntryCreate, FitnessStatsResponse

logger = logging.getLogger(__name__)


# ===== Weight Entry CRUD =====


def create_weight_entry(db: Session, user_id: int, data: WeightEntryCreate, source: str = "manual") -> WeightEntry:
    """Create a manual weight entry."""
    entry = WeightEntry(
        user_id=user_id,
        weight=data.weight,
        unit=data.unit,
        notes=data.notes,
        recorded_at=data.recorded_at,
        source=source,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_weight_history(db: Session, user_id: int, days: int = 90) -> list[WeightEntry]:
    """Get weight history for chart."""
    since = date.today() - timedelta(days=days)
    stmt = select(WeightEntry).where(
        and_(
            WeightEntry.user_id == user_id,
            WeightEntry.recorded_at >= since,
        )
    ).order_by(WeightEntry.recorded_at.asc())
    result = db.execute(stmt)
    return list(result.scalars().all())


def get_weight_entry(db: Session, entry_id: int, user_id: int) -> Optional[WeightEntry]:
    """Get a specific weight entry."""
    stmt = select(WeightEntry).where(
        and_(WeightEntry.id == entry_id, WeightEntry.user_id == user_id)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def delete_weight_entry(db: Session, entry_id: int, user_id: int) -> bool:
    """Delete a weight entry."""
    entry = get_weight_entry(db, entry_id, user_id)
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


# ===== Garmin Credentials CRUD =====


def get_garmin_credentials(db: Session, user_id: int) -> Optional[GarminCredential]:
    """Get Garmin credentials for a user."""
    stmt = select(GarminCredential).where(GarminCredential.user_id == user_id)
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def save_garmin_credentials(
    db: Session,
    user_id: int,
    email: str,
    tokens_json: str,
    garmin_username: Optional[str] = None,
) -> GarminCredential:
    """Save or update Garmin credentials."""
    from app.core.encryption import encrypt_password
    encrypted_tokens = encrypt_password(tokens_json)

    cred = get_garmin_credentials(db, user_id)
    if cred:
        cred.email = email
        cred.encrypted_tokens = encrypted_tokens
        cred.sync_enabled = True
        cred.sync_status = "ok"
        cred.sync_error = None
        if garmin_username:
            cred.garmin_username = garmin_username
    else:
        cred = GarminCredential(
            user_id=user_id,
            email=email,
            garmin_username=garmin_username,
            encrypted_tokens=encrypted_tokens,
            sync_enabled=True,
            sync_status="ok",
        )
        db.add(cred)

    db.commit()
    db.refresh(cred)
    return cred


def delete_garmin_credentials(db: Session, user_id: int) -> bool:
    """Remove Garmin credentials."""
    cred = get_garmin_credentials(db, user_id)
    if not cred:
        return False
    db.delete(cred)
    db.commit()
    return True


def update_garmin_sync_status(
    db: Session,
    user_id: int,
    status: str,
    error: Optional[str] = None,
    tokens_json: Optional[str] = None,
) -> None:
    """Update sync status after a sync attempt."""
    cred = get_garmin_credentials(db, user_id)
    if not cred:
        return
    cred.sync_status = status
    cred.sync_error = error
    cred.last_synced_at = datetime.now()
    if tokens_json:
        from app.core.encryption import encrypt_password
        cred.encrypted_tokens = encrypt_password(tokens_json)
    db.commit()


def load_garth_client(db: Session, user_id: int):
    """Load a garth client from stored credentials. Returns None if not found."""
    try:
        import garth
    except ImportError:
        logger.error("garth package not installed. Run: pip install garth")
        return None

    cred = get_garmin_credentials(db, user_id)
    if not cred or not cred.encrypted_tokens:
        return None

    try:
        from app.core.encryption import decrypt_password
        tokens_json = decrypt_password(cred.encrypted_tokens)
        tokens = json.loads(tokens_json)

        with tempfile.TemporaryDirectory() as tmpdir:
            for fname, data in tokens.items():
                fpath = os.path.join(tmpdir, fname)
                with open(fpath, 'w') as f:
                    json.dump(data, f)
            client = garth.Client(domain="garmin.com")
            client.load(tmpdir)

        return client
    except Exception as e:
        logger.error(f"Failed to load garth client for user {user_id}: {e}")
        return None


def serialize_garth_tokens(client) -> str:
    """Serialize garth client tokens to a JSON string for DB storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        client.dump(tmpdir)
        tokens = {}
        for fname in os.listdir(tmpdir):
            fpath = os.path.join(tmpdir, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath) as f:
                        tokens[fname] = json.load(f)
                except Exception:
                    pass
    return json.dumps(tokens)


# ===== Garmin Daily Stats CRUD =====


def upsert_garmin_daily_stat(
    db: Session,
    user_id: int,
    stat_date: date,
    steps: Optional[int] = None,
    active_calories: Optional[int] = None,
    sleep_minutes: Optional[int] = None,
    resting_hr: Optional[int] = None,
) -> GarminDailyStat:
    """Insert or update a daily Garmin stat record."""
    stmt = select(GarminDailyStat).where(
        and_(GarminDailyStat.user_id == user_id, GarminDailyStat.date == stat_date)
    )
    result = db.execute(stmt)
    stat = result.scalar_one_or_none()

    if stat:
        if steps is not None:
            stat.steps = steps
        if active_calories is not None:
            stat.active_calories = active_calories
        if sleep_minutes is not None:
            stat.sleep_minutes = sleep_minutes
        if resting_hr is not None:
            stat.resting_hr = resting_hr
        stat.synced_at = datetime.now()
    else:
        stat = GarminDailyStat(
            user_id=user_id,
            date=stat_date,
            steps=steps,
            active_calories=active_calories,
            sleep_minutes=sleep_minutes,
            resting_hr=resting_hr,
        )
        db.add(stat)

    db.commit()
    db.refresh(stat)
    return stat


def get_garmin_daily_stat(db: Session, user_id: int, stat_date: date) -> Optional[GarminDailyStat]:
    """Get daily stats for a specific date."""
    stmt = select(GarminDailyStat).where(
        and_(GarminDailyStat.user_id == user_id, GarminDailyStat.date == stat_date)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


# ===== Garmin Activities CRUD =====


def upsert_garmin_activity(
    db: Session,
    user_id: int,
    garmin_activity_id: str,
    activity_type: Optional[str] = None,
    name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    duration_minutes: Optional[int] = None,
    distance_km: Optional[float] = None,
    calories: Optional[int] = None,
    avg_hr: Optional[int] = None,
) -> GarminActivity:
    """Insert or update a Garmin activity."""
    stmt = select(GarminActivity).where(
        and_(
            GarminActivity.user_id == user_id,
            GarminActivity.garmin_activity_id == garmin_activity_id,
        )
    )
    result = db.execute(stmt)
    activity = result.scalar_one_or_none()

    if activity:
        activity.activity_type = activity_type or activity.activity_type
        activity.name = name or activity.name
        activity.start_time = start_time or activity.start_time
        activity.duration_minutes = duration_minutes if duration_minutes is not None else activity.duration_minutes
        activity.distance_km = distance_km if distance_km is not None else activity.distance_km
        activity.calories = calories if calories is not None else activity.calories
        activity.avg_hr = avg_hr if avg_hr is not None else activity.avg_hr
    else:
        activity = GarminActivity(
            user_id=user_id,
            garmin_activity_id=garmin_activity_id,
            activity_type=activity_type,
            name=name,
            start_time=start_time,
            duration_minutes=duration_minutes,
            distance_km=distance_km,
            calories=calories,
            avg_hr=avg_hr,
        )
        db.add(activity)

    db.commit()
    db.refresh(activity)
    return activity


def get_recent_activities(db: Session, user_id: int, days: int = 30, limit: int = 20) -> list[GarminActivity]:
    """Get recent activities."""
    since = datetime.now() - timedelta(days=days)
    stmt = select(GarminActivity).where(
        and_(
            GarminActivity.user_id == user_id,
            GarminActivity.start_time >= since,
        )
    ).order_by(desc(GarminActivity.start_time)).limit(limit)
    result = db.execute(stmt)
    return list(result.scalars().all())


# ===== Aggregated Widget Data =====


def get_fitness_stats(db: Session, user_id: int, days: int = 30, unit: str = "lbs") -> FitnessStatsResponse:
    """Build aggregated fitness stats response for the widget."""
    today = date.today()

    # Get today's Garmin stats
    today_stat = get_garmin_daily_stat(db, user_id, today)
    # Fall back to yesterday if today has no data yet (sync may not have run)
    if not today_stat or (today_stat.steps is None and today_stat.sleep_minutes is None):
        yesterday_stat = get_garmin_daily_stat(db, user_id, today - timedelta(days=1))
        display_stat = yesterday_stat or today_stat
    else:
        display_stat = today_stat

    # Get weight history
    weight_history = get_weight_history(db, user_id, days=days)

    # Convert to display unit if needed
    converted_history = []
    for entry in weight_history:
        entry_unit = entry.unit or "lbs"
        weight_val = float(entry.weight)
        if entry_unit != unit:
            if unit == "kg" and entry_unit == "lbs":
                weight_val = round(weight_val * 0.453592, 1)
            elif unit == "lbs" and entry_unit == "kg":
                weight_val = round(weight_val * 2.20462, 1)
        converted_history.append(entry)

    # Get latest weight entry
    latest_weight_entry = weight_history[-1] if weight_history else None

    # Get Garmin credentials for status
    cred = get_garmin_credentials(db, user_id)

    # Get recent activities
    recent_activities = get_recent_activities(db, user_id, days=days, limit=5)

    return FitnessStatsResponse(
        today_steps=display_stat.steps if display_stat else None,
        today_active_calories=display_stat.active_calories if display_stat else None,
        today_sleep_minutes=display_stat.sleep_minutes if display_stat else None,
        today_resting_hr=display_stat.resting_hr if display_stat else None,
        latest_weight=float(latest_weight_entry.weight) if latest_weight_entry else None,
        latest_weight_unit=latest_weight_entry.unit if latest_weight_entry else unit,
        latest_weight_date=latest_weight_entry.recorded_at if latest_weight_entry else None,
        weight_history=weight_history,
        recent_activities=recent_activities,
        garmin_connected=cred is not None,
        garmin_sync_status=cred.sync_status if cred else "never",
        garmin_last_synced_at=cred.last_synced_at if cred else None,
    )
