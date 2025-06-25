# filepath: tests/api/v1/test_projects.py
from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session
import uuid
from app.models.project import Project
from app.models.document_version import DocumentVersion
from app.main import app
from app.api.deps import get_db
from app.crud.project_crud import project_crud
from app.crud.document_version_crud import document_version_crud

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, session: Session):
    # Generate unique username and email
    unique_id = uuid.uuid4().hex[:8]
    
    # Create a test user
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 200
    user_id = response.json()["id"]
    
    # Login to get the authentication token
    login_data = {
        "username": f"testuser_{unique_id}",
        "password": "testpass123"
    }
    response = client.post("/api/v1/users/token", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    return {"headers": headers, "user_id": user_id}

def test_create_project_with_initial_version(client: TestClient, session: Session, auth_headers):
    # Get auth headers and user_id
    headers = auth_headers["headers"]
    user_id = auth_headers["user_id"]
    
    # Test project creation with a unique name
    unique_id = uuid.uuid4().hex[:8]
    response = client.post(
        "/api/v1/projects/",
        json={
            "name": f"Test Project {unique_id}",
            "repo_path": "/path/to/repo",
            "note": "Test note",
            "meta_data": "Test metadata",
            "created_by": user_id,
            "updated_by": user_id
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == f"Test Project {unique_id}"
    assert data["repo_path"] == "/path/to/repo"
    assert data["note"] == "Test note"
    assert data["current_version"] is not None
    
    # Get the project ID
    project_id = data["id"]
    current_version_id = data["current_version"]
    
    # Make API call to get the project details again
    response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    project_data = response.json()
    assert project_data["name"] == f"Test Project {unique_id}"
    
    # Get all document versions for the project
    response = client.get(f"/api/v1/document-versions/project/{project_id}", headers=headers)
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 1
    assert versions[0]["version_label"] == "v0"
    assert versions[0]["is_current"] == True
    
    # Verify the current_version in project points to the v0 version
    assert data["current_version"] == versions[0]["id"]
    
    # Get the current version through the API
    response = client.get(f"/api/v1/document-versions/project/{project_id}/current", headers=headers)
    assert response.status_code == 200
    current_version = response.json()
    assert current_version["version_label"] == "v0"
    assert current_version["is_current"] == True

def test_create_project_duplicate_name(client: TestClient, session: Session, auth_headers):
    # Get auth headers and user_id
    headers = auth_headers["headers"]
    user_id = auth_headers["user_id"]
    
    # Create a project with a specific name
    project_name = f"Duplicate Project {uuid.uuid4().hex[:8]}"
    
    # Create first project
    response = client.post(
        "/api/v1/projects/",
        json={
            "name": project_name,
            "repo_path": "/path/to/repo",
            "meta_data": "Test metadata",
            "created_by": user_id,
            "updated_by": user_id
        },
        headers=headers
    )
    assert response.status_code == 200
    
    # Try to create project with same name
    response = client.post(
        "/api/v1/projects/",
        json={
            "name": project_name,
            "repo_path": "/path/to/other/repo",
            "meta_data": "Another test metadata",
            "created_by": user_id,
            "updated_by": user_id
        },
        headers=headers
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

