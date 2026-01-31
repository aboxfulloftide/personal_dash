# Task 003: Authentication System

## Objective
Implement JWT-based authentication with registration, login, token refresh, and password reset functionality.

## Prerequisites
- Task 002 completed
- All database tables created

## Dependencies to Install
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
pip freeze > requirements.txt
```

## Deliverables

### 1. Security Utilities

#### app/core/security.py:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    return pwd_context.hash(token)

def verify_token_hash(token: str, hashed: str) -> bool:
    return pwd_context.verify(token, hashed)
```

### 2. Pydantic Schemas

#### app/schemas/auth.py:
```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class MessageResponse(BaseModel):
    message: str
```

#### app/schemas/__init__.py:
```python
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token,
    TokenRefresh, PasswordResetRequest, PasswordReset,
    PasswordChange, MessageResponse
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "Token",
    "TokenRefresh", "PasswordResetRequest", "PasswordReset",
    "PasswordChange", "MessageResponse"
]
```

### 3. Authentication Dependencies

#### app/core/dependencies.py:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

### 4. Auth Service

#### app/services/auth_service.py:
```python
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
```

### 5. Auth Endpoints

#### app/api/v1/endpoints/auth.py:
```python
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
```

### 6. Update Router

#### app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()
api_router.include_router(auth.router)
```

#### Create app/api/v1/endpoints/__init__.py:
```python
from app.api.v1.endpoints import auth
```

### 7. Unit Tests

#### tests/test_auth.py:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

class TestRegistration:
    def test_register_success(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123",
            "display_name": "Test User"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert "password" not in data

    def test_register_duplicate_email(self, client):
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        # Duplicate
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "anotherpassword123"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "short"
        })
        assert response.status_code == 422  # Validation error

class TestLogin:
    def test_login_success(self, client):
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

    def test_login_invalid_password(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        })
        assert response.status_code == 401

class TestProtectedRoutes:
    def test_get_me_authenticated(self, client):
        # Register and login
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Access protected route
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    def test_get_me_unauthenticated(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403  # No auth header

    def test_get_me_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401

class TestPasswordChange:
    def test_change_password_success(self, client):
        # Register and login
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == 200

        # Verify new password works
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "newpassword456"
        })
        assert login_response.status_code == 200
```

### 8. Run Tests

```bash
cd backend
pip install pytest pytest-cov
pytest tests/test_auth.py -v
```

## Acceptance Criteria
- [ ] User registration creates new user with hashed password
- [ ] User login returns access token and sets refresh token cookie
- [ ] Protected endpoints require valid access token
- [ ] Token refresh endpoint returns new access token
- [ ] Logout invalidates refresh token
- [ ] Password reset flow works (request -> reset)
- [ ] Password change works for authenticated users
- [ ] All unit tests pass

## Estimated Time
3-4 hours

## Next Task
Task 004: Frontend Authentication UI
