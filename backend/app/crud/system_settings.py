from sqlalchemy.orm import Session
from app.models.system_setting import SystemSetting

SPEEDTEST_DEFAULTS = {
    "speedtest_interval_hours": "6",
    "speedtest_retention_days": "30",
}


def get_setting(db: Session, key: str) -> str | None:
    row = db.get(SystemSetting, key)
    if row is not None:
        return row.value
    return SPEEDTEST_DEFAULTS.get(key)


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(SystemSetting, key)
    if row is None:
        row = SystemSetting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()


def get_speedtest_settings(db: Session) -> dict:
    return {
        "interval_hours": float(get_setting(db, "speedtest_interval_hours")),
        "retention_days": int(get_setting(db, "speedtest_retention_days")),
    }
