from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.auth import RefreshToken, PasswordResetToken
from app.schemas.auth import UserCreate
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_reset_token,
    hash_token, verify_token_hash
)
from app.core.config import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, user_data: UserCreate) -> User:
        # Check if email exists
        existing = self.db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            display_name=user_data.display_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    def create_tokens(self, user: User) -> Tuple[str, str]:
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token hash
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        self.db.add(token_record)
        self.db.commit()

        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Verify refresh token exists and is valid
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == int(user_id),
            RefreshToken.expires_at > datetime.utcnow()
        ).all()

        valid_token = None
        for token in tokens:
            if verify_token_hash(refresh_token, token.token_hash):
                valid_token = token
                break

        if not valid_token:
            return None

        # Verify user still exists and is active
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            return None

        # Create new access token
        return create_access_token(data={"sub": user_id})

    def logout(self, user_id: int, refresh_token: str) -> bool:
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).all()

        for token in tokens:
            if verify_token_hash(refresh_token, token.token_hash):
                self.db.delete(token)
                self.db.commit()
                return True
        return False

    def logout_all(self, user_id: int) -> int:
        result = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).delete()
        self.db.commit()
        return result

    def create_password_reset_token(self, email: str) -> Optional[str]:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None  # Don't reveal if email exists

        # Invalidate any existing reset tokens
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})

        token = generate_reset_token()
        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.db.add(reset_record)
        self.db.commit()

        return token

    def reset_password(self, token: str, new_password: str) -> bool:
        reset_tokens = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at > datetime.utcnow(),
            PasswordResetToken.used == False
        ).all()

        valid_reset = None
        for reset in reset_tokens:
            if verify_token_hash(token, reset.token_hash):
                valid_reset = reset
                break

        if not valid_reset:
            return False

        user = self.db.query(User).filter(User.id == valid_reset.user_id).first()
        if not user:
            return False

        user.password_hash = get_password_hash(new_password)
        valid_reset.used = True

        # Invalidate all refresh tokens (force re-login)
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).delete()

        self.db.commit()
        return True

    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        if not verify_password(current_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        return True