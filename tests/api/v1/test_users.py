# filepath: tests/api/v1/test_users.py
from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.models import User, Credential
from app.main import app
from app.api.deps import get_db
from app.crud.user_crud import user_crud
from app.crud.credential_crud import credential_crud
from app.core.security import verify_password

# Create a test database
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_user(client: TestClient, session: Session):
    # Test user creation
    response = client.post(
        "/api/v1/users/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data
    
    # Verify user exists in DB
    user = user_crud.get_by_username(session, "testuser")
    assert user is not None
    assert user.username == "testuser"
    
    # Verify credential exists in DB
    credential = credential_crud.get_by_user_id(session, user.id)
    assert credential is not None
    
    # Test login with the created user
    response = client.post(
        "/api/v1/users/login",
        data={
            "username": "testuser",
            "password": "password123"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test with incorrect password
    response = client.post(
        "/api/v1/users/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        },
    )
    assert response.status_code == 401
