from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.router import Router, RouterPollResult
from app.schemas.router import RouterCreate, RouterUpdate
from app.core.encryption import encrypt_password, decrypt_password


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_router(db: Session, user_id: int, router_in: RouterCreate) -> Router:
    router = Router(
        user_id=user_id,
        name=router_in.name,
        hostname=router_in.hostname,
        ssh_port=router_in.ssh_port,
        ssh_user=router_in.ssh_user,
        ssh_password_enc=encrypt_password(router_in.ssh_password) if router_in.ssh_password else None,
        ssh_key=router_in.ssh_key,
        poll_interval=router_in.poll_interval,
        script=router_in.script,
    )
    db.add(router)
    db.commit()
    db.refresh(router)
    return router


def get_routers(db: Session, user_id: int) -> list[Router]:
    result = db.execute(
        select(Router).where(Router.user_id == user_id).order_by(Router.created_at.desc())
    )
    return list(result.scalars().all())


def get_router(db: Session, router_id: int, user_id: int) -> Router | None:
    result = db.execute(
        select(Router).where(Router.id == router_id, Router.user_id == user_id)
    )
    return result.scalar_one_or_none()


def update_router(db: Session, router: Router, router_in: RouterUpdate) -> Router:
    if router_in.name is not None:
        router.name = router_in.name
    if router_in.hostname is not None:
        router.hostname = router_in.hostname
    if router_in.ssh_port is not None:
        router.ssh_port = router_in.ssh_port
    if router_in.ssh_user is not None:
        router.ssh_user = router_in.ssh_user
    if router_in.ssh_password is not None:
        router.ssh_password_enc = encrypt_password(router_in.ssh_password)
    if router_in.ssh_key is not None:
        router.ssh_key = router_in.ssh_key
    if router_in.poll_interval is not None:
        router.poll_interval = router_in.poll_interval
    if router_in.script is not None:
        router.script = router_in.script
    db.commit()
    db.refresh(router)
    return router


def delete_router(db: Session, router: Router) -> None:
    db.delete(router)
    db.commit()


def get_routers_due_for_poll(db: Session) -> list[Router]:
    """Return all routers where last_polled is None or past their poll_interval."""
    all_routers = db.execute(select(Router)).scalars().all()
    now = _now()
    due = []
    for r in all_routers:
        if r.last_polled is None:
            due.append(r)
        elif (now - r.last_polled).total_seconds() >= r.poll_interval:
            due.append(r)
    return due


def record_poll_result(
    db: Session, router: Router, is_online: bool,
    ping_ms: float | None, script_output: str | None,
) -> RouterPollResult:
    now = _now()
    result = RouterPollResult(
        router_id=router.id,
        is_online=is_online,
        ping_ms=ping_ms,
        script_output=script_output,
        recorded_at=now,
    )
    db.add(result)
    router.is_online = is_online
    router.ping_ms = ping_ms
    router.last_polled = now
    if is_online:
        router.last_seen = now
    db.commit()
    db.refresh(result)
    return result


def get_poll_history(db: Session, router_id: int, limit: int = 50) -> list[RouterPollResult]:
    result = db.execute(
        select(RouterPollResult)
        .where(RouterPollResult.router_id == router_id)
        .order_by(RouterPollResult.recorded_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def get_router_ssh_password(router: Router) -> str | None:
    if router.ssh_password_enc:
        return decrypt_password(router.ssh_password_enc)
    return None
