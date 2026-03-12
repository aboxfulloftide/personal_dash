from fastapi import APIRouter, HTTPException, status

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.crud.router import (
    create_router, get_routers, get_router, update_router,
    delete_router, get_poll_history,
)
from app.schemas.router import RouterCreate, RouterUpdate, RouterResponse, RouterPollResultResponse

router = APIRouter(prefix="/routers", tags=["Routers"])


def _to_response(r) -> RouterResponse:
    return RouterResponse(
        id=r.id,
        name=r.name,
        hostname=r.hostname,
        ssh_port=r.ssh_port,
        ssh_user=r.ssh_user,
        has_password=bool(r.ssh_password_enc),
        has_key=bool(r.ssh_key),
        poll_interval=r.poll_interval,
        script=r.script,
        is_online=r.is_online,
        ping_ms=r.ping_ms,
        last_seen=r.last_seen,
        last_polled=r.last_polled,
        created_at=r.created_at,
    )


@router.get("", response_model=list[RouterResponse])
def list_routers(db: DbSession, current_user: CurrentActiveUser):
    return [_to_response(r) for r in get_routers(db, current_user.id)]


@router.post("", response_model=RouterResponse, status_code=status.HTTP_201_CREATED)
def add_router(router_in: RouterCreate, db: DbSession, current_user: CurrentActiveUser):
    r = create_router(db, current_user.id, router_in)
    return _to_response(r)


@router.put("/{router_id}", response_model=RouterResponse)
def edit_router(router_id: int, router_in: RouterUpdate, db: DbSession, current_user: CurrentActiveUser):
    r = get_router(db, router_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Router not found")
    return _to_response(update_router(db, r, router_in))


@router.delete("/{router_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_router(router_id: int, db: DbSession, current_user: CurrentActiveUser):
    r = get_router(db, router_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Router not found")
    delete_router(db, r)


@router.get("/{router_id}/history", response_model=list[RouterPollResultResponse])
def router_poll_history(router_id: int, db: DbSession, current_user: CurrentActiveUser):
    r = get_router(db, router_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Router not found")
    return get_poll_history(db, router_id)


@router.post("/{router_id}/poll", response_model=RouterPollResultResponse)
def poll_router_now(router_id: int, db: DbSession, current_user: CurrentActiveUser):
    """Trigger an immediate poll of this router."""
    from app.core.router_poller import poll_router
    r = get_router(db, router_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Router not found")
    result = poll_router(db, r)
    return result
