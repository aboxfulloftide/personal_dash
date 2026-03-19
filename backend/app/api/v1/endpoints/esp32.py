from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.models.esp32 import Esp32Device
from app.core.config import settings

router = APIRouter(prefix="/esp32", tags=["ESP32"])

# Lazy wireless DB engine
_wireless_engine = None


def _get_wireless_engine():
    global _wireless_engine
    if _wireless_engine is None:
        if not settings.WIRELESS_DB_URL:
            raise HTTPException(status_code=503, detail="Wireless database not configured")
        _wireless_engine = create_engine(
            settings.WIRELESS_DB_URL,
            pool_pre_ping=True,
        )
    return _wireless_engine


def _wireless_session():
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=_get_wireless_engine())
    return Session()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class Esp32DeviceCreate(BaseModel):
    scanner_host: str
    display_name: str


class Esp32DeviceResponse(BaseModel):
    id: int
    scanner_host: str
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ScannerHealthRecord(BaseModel):
    scanner_host: str
    mac: str | None
    free_heap: int | None
    min_free_heap: int | None
    uptime_ms: int | None
    temperature_c: float | None
    recorded_at: datetime
    is_online: bool


class Esp32DeviceStatus(BaseModel):
    device: Esp32DeviceResponse
    health: ScannerHealthRecord | None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fetch_latest_health(scanner_host: str) -> ScannerHealthRecord | None:
    try:
        ws = _wireless_session()
        try:
            row = ws.execute(
                text(
                    "SELECT scanner_host, mac, free_heap, min_free_heap, uptime_ms, "
                    "temperature_c, recorded_at, "
                    "TIMESTAMPDIFF(SECOND, recorded_at, NOW()) <= 120 AS is_online "
                    "FROM scanner_health WHERE scanner_host = :host "
                    "ORDER BY recorded_at DESC LIMIT 1"
                ),
                {"host": scanner_host},
            ).fetchone()
        finally:
            ws.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Wireless DB error: {e}")

    if not row:
        return None
    return ScannerHealthRecord(
        scanner_host=row[0],
        mac=row[1],
        free_heap=row[2],
        min_free_heap=row[3],
        uptime_ms=row[4],
        temperature_c=float(row[5]) if row[5] is not None else None,
        recorded_at=row[6],
        is_online=bool(row[7]),
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/available-hosts", response_model=list[str])
def list_available_hosts(current_user: CurrentActiveUser):
    """Return distinct scanner_host values seen in the last 7 days."""
    try:
        ws = _wireless_session()
        try:
            rows = ws.execute(
                text(
                    "SELECT DISTINCT scanner_host FROM scanner_health "
                    "WHERE recorded_at >= NOW() - INTERVAL 7 DAY "
                    "ORDER BY scanner_host"
                )
            ).fetchall()
        finally:
            ws.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Wireless DB error: {e}")
    return [r[0] for r in rows]


@router.get("/devices", response_model=list[Esp32DeviceResponse])
def list_devices(db: DbSession, current_user: CurrentActiveUser):
    """List tracked ESP32 devices for the current user."""
    devices = db.query(Esp32Device).filter(Esp32Device.user_id == current_user.id).all()
    return [Esp32DeviceResponse.model_validate(d) for d in devices]


@router.post("/devices", response_model=Esp32DeviceResponse, status_code=status.HTTP_201_CREATED)
def add_device(device_in: Esp32DeviceCreate, db: DbSession, current_user: CurrentActiveUser):
    """Track a new ESP32 device."""
    device = Esp32Device(
        user_id=current_user.id,
        scanner_host=device_in.scanner_host.strip(),
        display_name=device_in.display_name.strip() or device_in.scanner_host.strip(),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return Esp32DeviceResponse.model_validate(device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device(device_id: int, db: DbSession, current_user: CurrentActiveUser):
    """Remove a tracked ESP32 device."""
    device = db.query(Esp32Device).filter(
        Esp32Device.id == device_id,
        Esp32Device.user_id == current_user.id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()


@router.get("/devices/status", response_model=list[Esp32DeviceStatus])
def get_devices_status(db: DbSession, current_user: CurrentActiveUser):
    """Get latest scanner_health data for all tracked devices."""
    devices = db.query(Esp32Device).filter(Esp32Device.user_id == current_user.id).all()
    result = []
    for d in devices:
        health = _fetch_latest_health(d.scanner_host)
        result.append(Esp32DeviceStatus(
            device=Esp32DeviceResponse.model_validate(d),
            health=health,
        ))
    return result


@router.get("/devices/{device_id}/history", response_model=list[ScannerHealthRecord])
def get_device_history(
    device_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
    hours: int = 1,
):
    """Get recent scanner_health history for a device."""
    device = db.query(Esp32Device).filter(
        Esp32Device.id == device_id,
        Esp32Device.user_id == current_user.id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        ws = _wireless_session()
        try:
            rows = ws.execute(
                text(
                    "SELECT scanner_host, mac, free_heap, min_free_heap, uptime_ms, "
                    "temperature_c, recorded_at, "
                    "TIMESTAMPDIFF(SECOND, recorded_at, NOW()) <= 120 AS is_online "
                    "FROM scanner_health WHERE scanner_host = :host "
                    "AND recorded_at >= NOW() - INTERVAL :hours HOUR "
                    "ORDER BY recorded_at ASC"
                ),
                {"host": device.scanner_host, "hours": max(1, min(hours, 168))},
            ).fetchall()
        finally:
            ws.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Wireless DB error: {e}")

    return [
        ScannerHealthRecord(
            scanner_host=r[0],
            mac=r[1],
            free_heap=r[2],
            min_free_heap=r[3],
            uptime_ms=r[4],
            temperature_c=float(r[5]) if r[5] is not None else None,
            recorded_at=r[6],
            is_online=bool(r[7]),
        )
        for r in rows
    ]
