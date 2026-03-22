"""
Personal Dash — Central Auth Integration Helper
================================================

Drop this file into any Python/FastAPI app on the same server to validate
Personal Dash JWTs and enforce per-app access levels.

Requirements:
    pip install python-jose[cryptography]

Environment variable:
    PERSONAL_DASH_SECRET_KEY  — same value as SECRET_KEY in personal_dash/backend/.env

Usage:
    from auth_integration import require_access, ACCESS_LEVELS

    # In a FastAPI endpoint:
    @app.get("/protected")
    def protected(payload: dict = Depends(require_viewer)):
        return {"user_id": payload["sub"], "apps": payload["apps"]}
"""

import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# ─── Config ──────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("PERSONAL_DASH_SECRET_KEY", "")
ALGORITHM = "HS256"
LEEWAY_SECONDS = 30

# The slug you registered for this app in the Admin → Apps panel.
# Change this to match your app's slug.
APP_SLUG = "netscan"  # <-- set your app slug here

ACCESS_LEVELS = {"none": 0, "viewer": 1, "user": 2, "admin": 3}


# ─── Core validation ─────────────────────────────────────────────────────────

def validate_token(token: str, app_slug: str = APP_SLUG, min_level: str = "viewer") -> dict:
    """Decode and validate a Personal Dash JWT.

    Returns the decoded payload on success.
    Raises ValueError with a descriptive message on failure.
    """
    if not SECRET_KEY:
        raise ValueError("PERSONAL_DASH_SECRET_KEY is not set")

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"leeway": LEEWAY_SECONDS},
        )
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {e}")

    if payload.get("type") != "access":
        raise ValueError("Not an access token")

    apps: dict[str, str] = payload.get("apps", {})
    level = apps.get(app_slug, "none")

    if ACCESS_LEVELS.get(level, 0) < ACCESS_LEVELS.get(min_level, 1):
        raise ValueError(f"Insufficient access: has '{level}', requires '{min_level}'")

    return payload


# ─── FastAPI dependency factories ─────────────────────────────────────────────

# Point this at your personal_dash backend login URL so Swagger UI works.
_oauth2 = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8000/api/v1/auth/login",
    auto_error=True,
)


def _make_dep(min_level: str):
    """Return a FastAPI dependency that requires the given access level."""

    def dependency(token: Annotated[str, Depends(_oauth2)]) -> dict:
        try:
            return validate_token(token, app_slug=APP_SLUG, min_level=min_level)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            )

    dependency.__name__ = f"require_{min_level}"
    return dependency


require_viewer = _make_dep("viewer")   # read-only access
require_user = _make_dep("user")       # standard user access
require_admin = _make_dep("admin")     # app-admin access

# ─── Example FastAPI integration ─────────────────────────────────────────────
#
# from fastapi import FastAPI, Depends
# from auth_integration import require_viewer, require_admin
#
# app = FastAPI()
#
# @app.get("/public-data")
# def public_data(payload: dict = Depends(require_viewer)):
#     return {"user_id": payload["sub"]}
#
# @app.post("/admin-action")
# def admin_action(payload: dict = Depends(require_admin)):
#     return {"ok": True}
