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
        assert response.status_code == 401  # No auth header

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