# filepath: app/api/v1/endpoints/project_artifacts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
import uuid

from app.schemas.project_artifact import ProjectArtifactCreate, ProjectArtifactRead, ProjectArtifactUpdate
from app.crud.project_artifact_crud import project_artifact_crud
from app.crud.project_crud import project_crud
from app.crud.document_version_crud import document_version_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.core.permissions import Permission
# from app.core.authz import require_permissions  # DEPRECATED
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ProjectArtifactRead)
def create_project_artifact(
    artifact: ProjectArtifactCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new project artifact (Manager/Tester only)"""
    # Check if project exists
    db_project = project_crud.get(db, project_id=artifact.project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    
    # Check if user can modify project content (Manager/Tester)
    if not current_user.can_modify_project_content(artifact.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers and testers can create artifacts"
        )
        
    # Check if version exists
    db_version = document_version_crud.get(db, doc_version_id=artifact.based_on_version)
    if db_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document version not found"
        )
    
    created_artifact = project_artifact_crud.create(db=db, obj_in=artifact)
    user_role = current_user.get_project_role(artifact.project_id)
    logger.info(f"User {current_user.username} ({user_role}) created artifact {artifact.artifact_type}")
    return created_artifact

@router.get("/{artifact_id}", response_model=ProjectArtifactRead)
def read_project_artifact(
    artifact_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project artifact by ID (All project members can read)"""
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    
    # Check if user is a member of the artifact's project
    if not current_user.is_project_member(db_artifact.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view this artifact"
        )
        
    return db_artifact

@router.get("/project/{project_id}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all artifacts for a specific project (All project members can read)"""
    # Check if project exists
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    
    # Check if user is a member of the project
    if not current_user.is_project_member(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view project artifacts"
        )
        
    artifacts = project_artifact_crud.get_by_project_id(db, project_id=project_id)
    user_role = current_user.get_project_role(project_id)
    logger.info(f"User {current_user.username} ({user_role}) read {len(artifacts)} artifacts for project")
    return artifacts

@router.get("/version/{version_id}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_version(
    version_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all artifacts based on a specific document version (All project members can read)"""
    # Check if version exists
    db_version = document_version_crud.get(db, doc_version_id=version_id)
    if db_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document version not found"
        )
    
    # Check if user is a member of the version's project
    if not current_user.is_project_member(db_version.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view artifacts for this version"
        )
        
    artifacts = project_artifact_crud.get_by_version(db, version_id=version_id)
    user_role = current_user.get_project_role(db_version.project_id)
    logger.info(f"User {current_user.username} ({user_role}) read {len(artifacts)} artifacts by version")
    return artifacts

@router.get("/type/{artifact_type}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_type(
    artifact_type: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get artifacts by type (Deprecated - returns only artifacts from user's projects)"""
    # This endpoint is problematic since it doesn't specify a project
    # For now, return empty list as users should use project-specific endpoints
    logger.warning(f"User {current_user.username} used deprecated artifacts-by-type endpoint")
    return []

@router.get("/", response_model=List[ProjectArtifactRead])
def read_project_artifacts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all project artifacts with pagination (Deprecated - returns only from user's projects)"""
    # This endpoint is problematic since it returns all artifacts across projects
    # For now, return empty list as users should use project-specific endpoints
    logger.warning(f"User {current_user.username} used deprecated get-all-artifacts endpoint")
    return []

@router.put("/{artifact_id}", response_model=ProjectArtifactRead)
def update_project_artifact(
    artifact_id: uuid.UUID, 
    artifact: ProjectArtifactUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project artifact (Manager/Tester only)"""
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    
    # Check if user can modify project content (Manager/Tester)
    if not current_user.can_modify_project_content(db_artifact.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers and testers can update artifacts"
        )
    
    updated_artifact = project_artifact_crud.update(db=db, id=artifact_id, obj_in=artifact)
    user_role = current_user.get_project_role(db_artifact.project_id)
    logger.info(f"User {current_user.username} ({user_role}) updated artifact {artifact_id}")
    return updated_artifact

@router.delete("/{artifact_id}", response_model=ProjectArtifactRead)
def delete_project_artifact(
    artifact_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project artifact (Manager only)"""
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    
    # Check if user can manage project (only managers can delete)
    if not current_user.can_manage_project_members(db_artifact.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers can delete artifacts"
        )
    
    deleted_artifact = project_artifact_crud.remove(db=db, id=artifact_id)
    if deleted_artifact:
        logger.info(f"Manager {current_user.username} deleted artifact {artifact_id}")
    return deleted_artifact

