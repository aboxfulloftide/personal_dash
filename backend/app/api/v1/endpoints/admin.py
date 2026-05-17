from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import CurrentAdminUser, DbSession
from app.crud.access import (
    get_all_users,
    get_app_by_id,
    get_app_by_slug,
    get_apps,
    create_app,
    update_app,
    delete_app,
    get_user_access,
    set_user_access,
    remove_user_access,
    user_access_entries,
    admin_create_user,
    admin_update_user,
    admin_delete_user,
)
from app.crud.user import get_user_by_email, get_user_by_id
from app.schemas.access import (
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    AppCreate,
    AppResponse,
    AppUpdate,
    SetAccessRequest,
    UserAccessEntry,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[AdminUserResponse])
def list_users(db: DbSession, current_user: CurrentAdminUser):
    """List all users with their app access."""
    users = get_all_users(db)
    result = []
    for u in users:
        result.append(
            AdminUserResponse(
                id=u.id,
                email=u.email,
                display_name=u.display_name,
                is_active=u.is_active,
                is_admin=u.is_admin,
                created_at=u.created_at,
                app_access=user_access_entries(db, u),
            )
        )
    return result


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: int, db: DbSession, current_user: CurrentAdminUser):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        app_access=user_access_entries(db, user),
    )


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: AdminUserCreate, db: DbSession, current_user: CurrentAdminUser):
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = admin_create_user(db, user_in)
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        app_access=[],
    )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(user_id: int, user_in: AdminUserUpdate, db: DbSession, current_user: CurrentAdminUser):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prevent admins from demoting themselves
    if user.id == current_user.id and user_in.is_admin is False:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin privileges")
    updated = admin_update_user(db, user, user_in)
    return AdminUserResponse(
        id=updated.id,
        email=updated.email,
        display_name=updated.display_name,
        is_active=updated.is_active,
        is_admin=updated.is_admin,
        created_at=updated.created_at,
        app_access=user_access_entries(db, updated),
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, current_user: CurrentAdminUser):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    admin_delete_user(db, user)


# ---------------------------------------------------------------------------
# App management
# ---------------------------------------------------------------------------

@router.get("/apps", response_model=list[AppResponse])
def list_apps(db: DbSession, current_user: CurrentAdminUser):
    return get_apps(db)


@router.post("/apps", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
def register_app(app_in: AppCreate, db: DbSession, current_user: CurrentAdminUser):
    if get_app_by_slug(db, app_in.slug):
        raise HTTPException(status_code=400, detail="App slug already exists")
    return create_app(db, app_in)


@router.patch("/apps/{app_id}", response_model=AppResponse)
def update_app_detail(app_id: int, app_in: AppUpdate, db: DbSession, current_user: CurrentAdminUser):
    app = get_app_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return update_app(db, app, app_in)


@router.delete("/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_app(app_id: int, db: DbSession, current_user: CurrentAdminUser):
    app = get_app_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    delete_app(db, app)


# ---------------------------------------------------------------------------
# User <-> App access management
# ---------------------------------------------------------------------------

@router.get("/users/{user_id}/access", response_model=list[UserAccessEntry])
def get_user_app_access(user_id: int, db: DbSession, current_user: CurrentAdminUser):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_access_entries(db, user)


@router.put("/users/{user_id}/access/{app_id}", response_model=UserAccessEntry)
def set_app_access(
    user_id: int,
    app_id: int,
    access_in: SetAccessRequest,
    db: DbSession,
    current_user: CurrentAdminUser,
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    app = get_app_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    entry = set_user_access(db, user_id, app_id, access_in.level)
    return UserAccessEntry(
        app_id=app.id,
        app_slug=app.slug,
        app_name=app.display_name,
        level=entry.level,
        granted_at=entry.granted_at,
    )


@router.delete("/users/{user_id}/access/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_app_access(
    user_id: int,
    app_id: int,
    db: DbSession,
    current_user: CurrentAdminUser,
):
    if not remove_user_access(db, user_id, app_id):
        raise HTTPException(status_code=404, detail="Access entry not found")


# ---------------------------------------------------------------------------
# System settings
# ---------------------------------------------------------------------------

class SpeedTestSettings(BaseModel):
    interval_hours: float = Field(..., ge=0.25, le=168, description="Hours between scheduled speed tests")
    retention_days: int = Field(..., ge=1, le=365, description="Days to keep speed test history")


@router.get("/settings/speedtest", response_model=SpeedTestSettings)
def get_speedtest_settings(db: DbSession, current_user: CurrentAdminUser):
    from app.crud.system_settings import get_speedtest_settings
    return get_speedtest_settings(db)


@router.put("/settings/speedtest", response_model=SpeedTestSettings)
def update_speedtest_settings(
    payload: SpeedTestSettings,
    db: DbSession,
    current_user: CurrentAdminUser,
):
    from app.crud.system_settings import set_setting, get_speedtest_settings
    set_setting(db, "speedtest_interval_hours", str(payload.interval_hours))
    set_setting(db, "speedtest_retention_days", str(payload.retention_days))
    return get_speedtest_settings(db)
