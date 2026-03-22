from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.access import App, UserAppAccess, ACCESS_LEVEL_RANK
from app.models.user import User
from app.schemas.access import AppCreate, AppUpdate, AdminUserCreate, AdminUserUpdate, UserAccessEntry
from app.core.security import get_password_hash


# ---------- Apps ----------

def get_apps(db: Session) -> list[App]:
    return list(db.execute(select(App).order_by(App.display_name)).scalars().all())


def get_app_by_id(db: Session, app_id: int) -> App | None:
    return db.execute(select(App).where(App.id == app_id)).scalar_one_or_none()


def get_app_by_slug(db: Session, slug: str) -> App | None:
    return db.execute(select(App).where(App.slug == slug)).scalar_one_or_none()


def create_app(db: Session, app_in: AppCreate) -> App:
    app = App(
        slug=app_in.slug,
        display_name=app_in.display_name,
        description=app_in.description,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_app(db: Session, app: App, app_in: AppUpdate) -> App:
    if app_in.display_name is not None:
        app.display_name = app_in.display_name
    if app_in.description is not None:
        app.description = app_in.description
    if app_in.is_active is not None:
        app.is_active = app_in.is_active
    db.commit()
    db.refresh(app)
    return app


def delete_app(db: Session, app: App) -> None:
    db.delete(app)
    db.commit()


# ---------- User app access ----------

def get_user_access(db: Session, user_id: int) -> list[UserAppAccess]:
    stmt = (
        select(UserAppAccess)
        .where(UserAppAccess.user_id == user_id)
        .join(UserAppAccess.app)
        .order_by(App.display_name)
    )
    return list(db.execute(stmt).scalars().all())


def set_user_access(db: Session, user_id: int, app_id: int, level: str) -> UserAppAccess:
    stmt = select(UserAppAccess).where(
        UserAppAccess.user_id == user_id,
        UserAppAccess.app_id == app_id,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        existing.level = level
        db.commit()
        db.refresh(existing)
        return existing

    entry = UserAppAccess(user_id=user_id, app_id=app_id, level=level)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def remove_user_access(db: Session, user_id: int, app_id: int) -> bool:
    stmt = select(UserAppAccess).where(
        UserAppAccess.user_id == user_id,
        UserAppAccess.app_id == app_id,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if not existing:
        return False
    db.delete(existing)
    db.commit()
    return True


def build_apps_claim(db: Session, user: User) -> dict[str, str]:
    """Return {app_slug: level} dict for embedding in JWT.

    Superadmins get 'admin' on every active app.
    """
    if user.is_admin:
        apps = get_apps(db)
        return {a.slug: "admin" for a in apps if a.is_active}

    access_rows = get_user_access(db, user.id)
    return {
        row.app.slug: row.level
        for row in access_rows
        if row.app.is_active and row.level != "none"
    }


def user_access_entries(db: Session, user: User) -> list[UserAccessEntry]:
    """Return structured access list for admin responses."""
    if user.is_admin:
        apps = get_apps(db)
        return [
            UserAccessEntry(
                app_id=a.id,
                app_slug=a.slug,
                app_name=a.display_name,
                level="admin",
                granted_at=a.created_at,
            )
            for a in apps
        ]

    rows = get_user_access(db, user.id)
    return [
        UserAccessEntry(
            app_id=row.app_id,
            app_slug=row.app.slug,
            app_name=row.app.display_name,
            level=row.level,
            granted_at=row.granted_at,
        )
        for row in rows
    ]


# ---------- Admin user management ----------

def get_all_users(db: Session) -> list[User]:
    return list(db.execute(select(User).order_by(User.email)).scalars().all())


def admin_create_user(db: Session, user_in: AdminUserCreate) -> User:
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        display_name=user_in.display_name,
        is_admin=user_in.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def admin_update_user(db: Session, user: User, user_in: AdminUserUpdate) -> User:
    if user_in.display_name is not None:
        user.display_name = user_in.display_name
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.is_admin is not None:
        user.is_admin = user_in.is_admin
    if user_in.password:
        user.password_hash = get_password_hash(user_in.password)
    db.commit()
    db.refresh(user)
    return user


def admin_delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
