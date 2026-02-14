from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get a user by email address."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get a user by ID."""
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Create a new user with hashed password."""
    db_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        display_name=user_in.display_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        # Run password verify anyway to prevent timing attacks (using valid dummy hash)
        verify_password(password, "$2b$12$U6lbIil8ilAxCjNYG3XHYuRcAZGm5AXfZgSOsZgsebSTbob4EA.Sm")
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
