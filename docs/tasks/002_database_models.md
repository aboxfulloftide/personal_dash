# Task 002: Database Models & Migrations

## Objective
Create SQLAlchemy models for all database tables and set up Alembic migrations.

## Prerequisites
- Task 001 completed
- MySQL database created
- Backend virtual environment activated
- .env file in backend dir that contains server creds
## Deliverables

### 1. Database Connection Setup

#### app/core/database.py:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2. SQLAlchemy Models

#### app/models/user.py:
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    widget_configs = relationship("WidgetConfig", back_populates="user", cascade="all, delete-orphan")
    dashboard_layouts = relationship("DashboardLayout", back_populates="user", cascade="all, delete-orphan")
    servers = relationship("Server", back_populates="user", cascade="all, delete-orphan")
    packages = relationship("Package", back_populates="user", cascade="all, delete-orphan")
    weight_entries = relationship("WeightEntry", back_populates="user", cascade="all, delete-orphan")
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
```

#### app/models/auth.py:
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
```

#### app/models/widget.py:
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    widget_type = Column(String(50), nullable=False)
    config = Column(JSON)
    layout = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="widget_configs")

class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    layout = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="dashboard_layouts")
```

#### app/models/server.py:
```python
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255))
    ip_address = Column(String(45))
    mac_address = Column(String(17))  # For Wake-on-LAN
    api_key_hash = Column(String(255), nullable=False)
    poll_interval = Column(Integer, default=60)  # seconds
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="servers")
    metrics = relationship("ServerMetric", back_populates="server", cascade="all, delete-orphan")
    containers = relationship("DockerContainer", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("ServerAlert", back_populates="server", cascade="all, delete-orphan")

class ServerMetric(Base):
    __tablename__ = "server_metrics"

    id = Column(BigInteger, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    network_in = Column(BigInteger)
    network_out = Column(BigInteger)
    recorded_at = Column(DateTime, server_default=func.now(), index=True)

    server = relationship("Server", back_populates="metrics")

class DockerContainer(Base):
    __tablename__ = "docker_containers"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    container_id = Column(String(64), nullable=False)
    name = Column(String(255))
    image = Column(String(255))
    status = Column(String(50))
    cpu_percent = Column(Float)
    memory_usage = Column(BigInteger)
    memory_limit = Column(BigInteger)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    server = relationship("Server", back_populates="containers")

class ServerAlert(Base):
    __tablename__ = "server_alerts"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # cpu, memory, disk, offline
    threshold = Column(Float)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    server = relationship("Server", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")

class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(BigInteger, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("server_alerts.id", ondelete="CASCADE"), nullable=False)
    triggered_value = Column(Float)
    message = Column(Text)
    acknowledged = Column(Boolean, default=False)
    triggered_at = Column(DateTime, server_default=func.now())

    alert = relationship("ServerAlert", back_populates="history")
```

#### app/models/package.py:
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tracking_number = Column(String(100), nullable=False)
    carrier = Column(String(50), nullable=False)  # usps, ups, fedex, amazon
    description = Column(String(255))
    status = Column(String(100))
    estimated_delivery = Column(Date)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime)
    source = Column(String(20), default="manual")  # manual, email
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="packages")
    events = relationship("PackageEvent", back_populates="package", cascade="all, delete-orphan")

class PackageEvent(Base):
    __tablename__ = "package_events"

    id = Column(BigInteger, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(255))
    location = Column(String(255))
    event_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    package = relationship("Package", back_populates="events")

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email_address = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # gmail, imap
    credentials_encrypted = Column(Text)  # Encrypted OAuth tokens or app passwords
    last_checked = Column(DateTime)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="email_accounts")
```

#### app/models/fitness.py:
```python
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    unit = Column(String(10), default="lbs")
    notes = Column(Text)
    recorded_at = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="weight_entries")
```

#### app/models/cache.py:
```python
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class APICache(Base):
    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
```

#### app/models/__init__.py:
```python
from app.models.user import User
from app.models.auth import RefreshToken, PasswordResetToken
from app.models.widget import WidgetConfig, DashboardLayout
from app.models.server import Server, ServerMetric, DockerContainer, ServerAlert, AlertHistory
from app.models.package import Package, PackageEvent, EmailAccount
from app.models.fitness import WeightEntry
from app.models.cache import APICache

__all__ = [
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "WidgetConfig",
    "DashboardLayout",
    "Server",
    "ServerMetric",
    "DockerContainer",
    "ServerAlert",
    "AlertHistory",
    "Package",
    "PackageEvent",
    "EmailAccount",
    "WeightEntry",
    "APICache",
]
```

### 3. Alembic Configuration

#### Update alembic.ini:
Change the sqlalchemy.url line to:
```ini
sqlalchemy.url = 
```
(Leave empty, we'll set it from env.py)

#### Update alembic/env.py:
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base
from app.models import *  # Import all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 4. Create Initial Migration

Run these commands:
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

### 5. Verify Tables

Connect to MySQL and verify:
```sql
USE personal_dash;
SHOW TABLES;
```

Expected tables:
- users
- refresh_tokens
- password_reset_tokens
- widget_configs
- dashboard_layouts
- servers
- server_metrics
- docker_containers
- server_alerts
- alert_history
- packages
- package_events
- email_accounts
- weight_entries
- api_cache
- alembic_version

## Acceptance Criteria
- [ ] All model files created with proper relationships
- [ ] alembic/env.py configured to use settings and import models
- [ ] `alembic revision --autogenerate` generates migration without errors
- [ ] `alembic upgrade head` applies migration successfully
- [ ] All 15 tables created in MySQL database
- [ ] Foreign keys and indexes properly set
- [ ] Relationships work (can query related objects)

## Estimated Time
2-3 hours

## Next Task
Task 003: Authentication System
