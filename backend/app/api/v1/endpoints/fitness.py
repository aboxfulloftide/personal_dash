"""API endpoints for fitness tracking."""
import json
import logging
import os
import tempfile
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select as sa_select

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, get_db
from app.crud import fitness as crud
from app.schemas.fitness import (
    WeightEntryCreate,
    WeightEntryResponse,
    GarminConnectRequest,
    GarminStatusResponse,
    GarminActivityResponse,
    FitnessStatsResponse,
)

router = APIRouter(prefix="/fitness", tags=["Fitness"])
logger = logging.getLogger(__name__)


# ===== Widget Stats Endpoint =====


@router.get("/stats", response_model=FitnessStatsResponse)
def get_fitness_stats(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=7, le=90),
    unit: str = Query("lbs", pattern="^(lbs|kg)$"),
):
    """Aggregated fitness stats for the widget."""
    return crud.get_fitness_stats(db, current_user.id, days=days, unit=unit)


# ===== Weight Endpoints =====


@router.get("/weight", response_model=list[WeightEntryResponse])
def get_weight_history(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    days: int = Query(90, ge=7, le=365),
):
    """Weight history for chart."""
    return crud.get_weight_history(db, current_user.id, days=days)


@router.post("/weight", response_model=WeightEntryResponse, status_code=201)
def log_weight(
    data: WeightEntryCreate,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Log a manual weight entry."""
    return crud.create_weight_entry(db, current_user.id, data, source="manual")


@router.delete("/weight/{entry_id}", status_code=204)
def delete_weight_entry(
    entry_id: int,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Delete a weight entry."""
    success = crud.delete_weight_entry(db, entry_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Weight entry not found")
    return None


# ===== Activities Endpoints =====


@router.get("/activities", response_model=list[GarminActivityResponse])
def get_activities(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=90),
):
    """Get recent activities from Garmin."""
    return crud.get_recent_activities(db, current_user.id, days=days, limit=20)


# ===== Garmin Endpoints =====


@router.get("/garmin/status", response_model=GarminStatusResponse)
def get_garmin_status(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Get Garmin connection status."""
    cred = crud.get_garmin_credentials(db, current_user.id)
    if not cred:
        return GarminStatusResponse(connected=False)
    return GarminStatusResponse(
        connected=True,
        email=cred.email,
        sync_enabled=cred.sync_enabled,
        last_synced_at=cred.last_synced_at,
        sync_status=cred.sync_status,
        sync_error=cred.sync_error,
    )


@router.post("/garmin/connect", response_model=GarminStatusResponse)
async def connect_garmin(
    request: GarminConnectRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """
    Connect a Garmin account by logging in with email/password.
    Stores OAuth tokens (password is NOT stored).
    """
    try:
        import garth
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Garmin integration not available (garth package not installed)",
        )

    try:
        client = garth.Client(domain="garmin.com")
        client.login(request.email, request.password)
    except Exception as e:
        err_str = str(e)
        if "MFA" in err_str or "2FA" in err_str or "TOTP" in err_str:
            raise HTTPException(
                status_code=400,
                detail="Garmin account has 2FA enabled. Please disable 2FA or use an app-specific password.",
            )
        raise HTTPException(status_code=401, detail=f"Garmin login failed: {err_str}")

    # Get Garmin display name for API calls
    garmin_username = None
    try:
        profile = client.connectapi("/userprofile-service/socialProfile")
        garmin_username = profile.get("displayName")
    except Exception as e:
        logger.warning(f"Could not fetch Garmin profile for user {current_user.id}: {e}")

    # Serialize tokens
    try:
        tokens_json = crud.serialize_garth_tokens(client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serialize Garmin tokens: {e}")

    # Save credentials
    cred = crud.save_garmin_credentials(
        db,
        current_user.id,
        request.email,
        tokens_json,
        garmin_username=garmin_username,
    )

    # Trigger initial sync in background
    background_tasks.add_task(_run_garmin_sync, current_user.id)

    return GarminStatusResponse(
        connected=True,
        email=cred.email,
        sync_enabled=cred.sync_enabled,
        last_synced_at=cred.last_synced_at,
        sync_status=cred.sync_status,
        sync_error=cred.sync_error,
    )


@router.post("/garmin/sync", response_model=GarminStatusResponse)
async def trigger_garmin_sync(
    background_tasks: BackgroundTasks,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Manually trigger a Garmin data sync."""
    cred = crud.get_garmin_credentials(db, current_user.id)
    if not cred:
        raise HTTPException(status_code=404, detail="No Garmin account connected")

    background_tasks.add_task(_run_garmin_sync, current_user.id)

    return GarminStatusResponse(
        connected=True,
        email=cred.email,
        sync_enabled=cred.sync_enabled,
        last_synced_at=cred.last_synced_at,
        sync_status=cred.sync_status,
        sync_error=cred.sync_error,
    )


@router.delete("/garmin/disconnect", status_code=204)
def disconnect_garmin(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """Remove Garmin credentials and stop sync."""
    success = crud.delete_garmin_credentials(db, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="No Garmin account connected")
    return None


# ===== Internal sync helper =====


async def _run_garmin_sync(user_id: int):
    """Run a Garmin sync for one user (called from background tasks and scheduler)."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        await sync_garmin_for_user(db, user_id, days_back=7)
    except Exception as e:
        logger.error(f"Garmin sync failed for user {user_id}: {e}")
    finally:
        db.close()


async def sync_garmin_for_user(db: Session, user_id: int, days_back: int = 7):
    """
    Sync Garmin data for a single user.
    Fetches daily stats, activities, and weight for the past days_back days.
    """
    try:
        import garth
    except ImportError:
        logger.error("garth package not installed")
        return

    cred = crud.get_garmin_credentials(db, user_id)
    if not cred or not cred.sync_enabled:
        return

    client = crud.load_garth_client(db, user_id)
    if not client:
        crud.update_garmin_sync_status(db, user_id, "error", "Failed to load credentials")
        return

    garmin_username = cred.garmin_username
    if not garmin_username:
        try:
            profile = client.connectapi("/userprofile-service/socialProfile")
            garmin_username = profile.get("displayName")
            if garmin_username:
                cred.garmin_username = garmin_username
                db.commit()
        except Exception as e:
            logger.warning(f"Could not fetch Garmin profile for user {user_id}: {e}")

    errors = []
    today = date.today()

    for days_ago in range(days_back):
        target_date = today - timedelta(days=days_ago)
        date_str = target_date.strftime("%Y-%m-%d")

        # Fetch daily summary (steps, active calories, resting HR)
        if garmin_username:
            try:
                summary = client.connectapi(
                    f"/usersummary-service/usersummary/daily/{garmin_username}",
                    params={"calendarDate": date_str},
                )
                steps = summary.get("totalSteps")
                active_cal = summary.get("activeKilocalories")
                resting_hr = summary.get("restingHeartRate")

                crud.upsert_garmin_daily_stat(
                    db, user_id, target_date,
                    steps=steps,
                    active_calories=active_cal,
                    resting_hr=resting_hr,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch daily summary for user {user_id} on {date_str}: {e}")
                errors.append(str(e))

            # Fetch sleep data
            try:
                sleep_data = client.connectapi(
                    f"/wellness-service/wellness/dailySleepData/{garmin_username}",
                    params={"date": date_str},
                )
                sleep_seconds = None
                if sleep_data and isinstance(sleep_data, dict):
                    dto = sleep_data.get("dailySleepDTO") or sleep_data
                    sleep_seconds = dto.get("sleepTimeSeconds")

                if sleep_seconds is not None:
                    crud.upsert_garmin_daily_stat(
                        db, user_id, target_date,
                        sleep_minutes=sleep_seconds // 60,
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch sleep data for user {user_id} on {date_str}: {e}")

    # Fetch activities for the full range
    try:
        start_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        activities = client.connectapi(
            "/activitylist-service/activities/search/activities",
            params={"startDate": start_date, "endDate": end_date, "limit": 50},
        )
        if activities and isinstance(activities, list):
            for act in activities:
                act_id = str(act.get("activityId", ""))
                if not act_id:
                    continue

                act_type = None
                if act.get("activityType"):
                    act_type = act["activityType"].get("typeKey")

                duration_sec = act.get("duration")
                duration_min = int(duration_sec // 60) if duration_sec else None

                distance_m = act.get("distance")
                distance_km = round(distance_m / 1000, 3) if distance_m else None

                start_time_str = act.get("startTimeLocal") or act.get("startTimeGMT")
                start_time = None
                if start_time_str:
                    try:
                        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

                crud.upsert_garmin_activity(
                    db, user_id, act_id,
                    activity_type=act_type,
                    name=act.get("activityName"),
                    start_time=start_time,
                    duration_minutes=duration_min,
                    distance_km=distance_km,
                    calories=act.get("calories"),
                    avg_hr=act.get("averageHR"),
                )
    except Exception as e:
        logger.warning(f"Failed to fetch activities for user {user_id}: {e}")
        errors.append(str(e))

    # Fetch Garmin weight data (from Index scale)
    try:
        start_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        weight_data = client.connectapi(
            "/weight-service/weight/dateRange",
            params={"startDate": start_date, "endDate": end_date},
        )
        if weight_data and isinstance(weight_data, dict):
            weight_list = weight_data.get("dateWeightList") or []
            for w in weight_list:
                weight_kg = w.get("weight")
                cal_date_str = w.get("calendarDate")
                if weight_kg and cal_date_str:
                    try:
                        w_date = date.fromisoformat(cal_date_str)
                        # Store in kg, convert later if needed
                        from app.schemas.fitness import WeightEntryCreate
                        entry_data = WeightEntryCreate(
                            weight=round(weight_kg / 1000, 2),  # Garmin stores in grams
                            unit="kg",
                            recorded_at=w_date,
                        )
                        # Only create if no manual entry exists for that date
                        from app.models.fitness import WeightEntry as WE
                        existing = db.execute(
                            sa_select(WE).where(
                                WE.user_id == user_id,
                                WE.recorded_at == w_date,
                            )
                        ).scalar_one_or_none()
                        if not existing:
                            crud.create_weight_entry(db, user_id, entry_data, source="garmin")
                    except Exception as e:
                        logger.warning(f"Failed to save Garmin weight entry: {e}")
    except Exception as e:
        logger.debug(f"No Garmin weight data for user {user_id}: {e}")

    # Save updated tokens (garth may have refreshed OAuth2 tokens)
    try:
        updated_tokens = crud.serialize_garth_tokens(client)
    except Exception:
        updated_tokens = None

    status = "error" if errors else "ok"
    error_msg = "; ".join(errors[:3]) if errors else None
    crud.update_garmin_sync_status(db, user_id, status, error_msg, tokens_json=updated_tokens)

    logger.info(f"Garmin sync completed for user {user_id}: {status}")
