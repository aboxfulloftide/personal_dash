from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.security import generate_refresh_token, hash_token, create_access_token
from app.crud.user import get_user_by_email, create_user, authenticate_user
from app.models.auth import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    MessageResponse,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.v1.deps import CurrentActiveUser, DbSession

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_in: UserCreate, db: DbSession) -> User:
    """Register a new user."""
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = create_user(db, user_in)
    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: DbSession) -> dict:
    """Authenticate user and return access + refresh tokens."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = generate_refresh_token()

    # Store as naive datetime (MySQL doesn't store timezone info)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
    )
    db.add(db_refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_data: RefreshRequest, db: DbSession) -> dict:
    """Exchange a valid refresh token for new tokens."""
    token_hash = hash_token(refresh_data.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    db_token = db.execute(stmt).scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Compare as naive datetimes (MySQL stores without timezone)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    if db_token.expires_at < now_utc:
        db.delete(db_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db_token.user
    if not user or not user.is_active:
        db.delete(db_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db.delete(db_token)

    access_token = create_access_token(subject=user.id)
    new_refresh_token = generate_refresh_token()

    # Store as naive datetime (MySQL doesn't store timezone info)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    new_db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=expires_at,
    )
    db.add(new_db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=MessageResponse)
def logout(
    logout_data: LogoutRequest, db: DbSession, current_user: CurrentActiveUser
) -> dict:
    """Invalidate a refresh token."""
    token_hash = hash_token(logout_data.refresh_token)

    stmt = delete(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.user_id == current_user.id,
    )
    db.execute(stmt)
    db.commit()

    return {"message": "Successfully logged out"}


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(db: DbSession, current_user: CurrentActiveUser) -> dict:
    """Invalidate all refresh tokens for the current user."""
    stmt = delete(RefreshToken).where(RefreshToken.user_id == current_user.id)
    db.execute(stmt)
    db.commit()

    return {"message": "Successfully logged out from all devices"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: CurrentActiveUser) -> User:
    """Get the current authenticated user's information."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    user_in: UserUpdate, db: DbSession, current_user: CurrentActiveUser
) -> User:
    """Update the current authenticated user's profile."""
    if user_in.display_name is not None:
        current_user.display_name = user_in.display_name
    if user_in.favicon_url is not None:
        current_user.favicon_url = user_in.favicon_url
    elif "favicon_url" in user_in.model_fields_set:
        current_user.favicon_url = None
    db.commit()
    db.refresh(current_user)
    return current_user
