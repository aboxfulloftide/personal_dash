from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token,
    PasswordResetRequest, PasswordReset, PasswordChange, MessageResponse
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    service = AuthService(db)
    user = service.register(user_data)
    return user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login and receive access token. Refresh token set in httpOnly cookie."""
    service = AuthService(db)
    user = service.authenticate(user_data.email, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token, refresh_token = service.create_tokens(user)

    # Set refresh token in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 28  # 28 days
    )

    return Token(access_token=access_token)

@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None)
):
    """Get new access token using refresh token from cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    service = AuthService(db)
    new_access_token = service.refresh_access_token(refresh_token)

    if not new_access_token:
        response.delete_cookie("refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return Token(access_token=new_access_token)

@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh_token: Optional[str] = Cookie(None)
):
    """Logout current session."""
    if refresh_token:
        service = AuthService(db)
        service.logout(current_user.id, refresh_token)

    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out successfully")

@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout all sessions for current user."""
    service = AuthService(db)
    count = service.logout_all(current_user.id)
    response.delete_cookie("refresh_token")
    return MessageResponse(message=f"Logged out from {count} session(s)")

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@router.post("/password-reset-request", response_model=MessageResponse)
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset email."""
    service = AuthService(db)
    token = service.create_password_reset_token(data.email)

    if token:
        # TODO: Send email with reset link containing token
        # For development, you can log the token
        print(f"Password reset token for {data.email}: {token}")

    # Always return success to not reveal if email exists
    return MessageResponse(message="If the email exists, a reset link has been sent")

@router.post("/password-reset", response_model=MessageResponse)
def reset_password(data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using token from email."""
    service = AuthService(db)
    success = service.reset_password(data.token, data.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return MessageResponse(message="Password reset successfully")

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    service = AuthService(db)
    success = service.change_password(current_user, data.current_password, data.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    return MessageResponse(message="Password changed successfully")