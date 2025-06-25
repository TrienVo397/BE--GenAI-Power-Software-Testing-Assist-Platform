# filepath: tests/api/v1/test_project_artifacts.py
import pytest
from fastapi.testclient import TestClient
import uuid
import sys

print("DEBUG: test_project_artifacts.py is being imported", file=sys.stderr)

from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_create_project_artifact(db):
    # Generate unique username and email using uuid
    unique_id = uuid.uuid4().hex[:8]
    
    # First, create a user with unique username and email
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "testpass123",
        "full_name": "Test Artifact User"
    }
    response = client.post("/api/v1/users/register", json=user_data)
    print(f"DEBUG: User registration response - {response.status_code}: {response.text}")
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
    
    # Create a project with unique name
    project_data = {
        "name": f"Test Project for Artifacts_{unique_id}",
        "repo_path": f"/test/artifact/repo/{unique_id}",
        "note": "Test project for artifact tests",
        "meta_data": "Test metadata",
        "created_by": user_id,
        "updated_by": user_id
    }
    
    response = client.post("/api/v1/projects/", json=project_data, headers=headers)
    print(f"DEBUG: Project creation response - {response.status_code}: {response.text}")
    assert response.status_code == 200
    project_id = response.json()["id"]
    version_id = response.json()["current_version"]
    
    # Create a project artifact
    artifact_data = {
        "project_id": project_id,
        "based_on_version": version_id,
        "artifact_type": "test_report",
        "file_path": "/path/to/test/report.pdf",
        "note": "Test artifact",
        "meta_data": "Test artifact metadata",
        "created_by": user_id,
        "updated_by": user_id
    }
    
    response = client.post("/api/v1/project-artifacts/", json=artifact_data, headers=headers)
    assert response.status_code == 200
    artifact_id = response.json()["id"]
    
    # Verify the artifact was created correctly
    response = client.get(f"/api/v1/project-artifacts/{artifact_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_type"] == "test_report"
    assert data["file_path"] == "/path/to/test/report.pdf"
    
    # Get artifacts by project
    response = client.get(f"/api/v1/project-artifacts/project/{project_id}", headers=headers)
    assert response.status_code == 200
    artifacts = response.json()
    assert len(artifacts) == 1
    assert artifacts[0]["id"] == artifact_id
    
    # Get artifacts by version
    response = client.get(f"/api/v1/project-artifacts/version/{version_id}", headers=headers)
    assert response.status_code == 200
    artifacts = response.json()
    assert len(artifacts) == 1
    assert artifacts[0]["id"] == artifact_id
    
    # Get artifacts by type
    response = client.get(f"/api/v1/project-artifacts/type/test_report", headers=headers)
    assert response.status_code == 200
    artifacts = response.json()
    assert len(artifacts) > 0
    
    # Update the artifact
    update_data = {
        "artifact_type": "updated_test_report",
        "deprecated": True,
        "deprecated_reason": "Test update",
        "updated_by": user_id
    }
    
    response = client.put(f"/api/v1/project-artifacts/{artifact_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    updated_artifact = response.json()
    assert updated_artifact["artifact_type"] == "updated_test_report"
    assert updated_artifact["deprecated"] == True
    assert updated_artifact["deprecated_reason"] == "Test update"
    
    # Delete the artifact
    response = client.delete(f"/api/v1/project-artifacts/{artifact_id}", headers=headers)
    assert response.status_code == 200
    
    # Verify its gone
    response = client.get(f"/api/v1/project-artifacts/{artifact_id}", headers=headers)
    assert response.status_code == 404

