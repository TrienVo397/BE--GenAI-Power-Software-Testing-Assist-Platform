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
from app.core.authz import require_permissions
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ProjectArtifactRead)
def create_project_artifact(
    artifact: ProjectArtifactCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_CREATE))
):
    """Create new project artifact (Manager/Tester only)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only managers and testers can create artifacts."
        )
    
    # Check if project exists
    db_project = project_crud.get(db, project_id=artifact.project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
        
    # Check if version exists
    db_version = document_version_crud.get(db, doc_version_id=artifact.based_on_version)
    if db_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document version not found"
        )
    
    created_artifact = project_artifact_crud.create(db=db, obj_in=artifact)
    logger.info(f"User {current_user.username} ({current_user.get_roles()}) created artifact {artifact.artifact_type}")
    return created_artifact

@router.get("/{artifact_id}", response_model=ProjectArtifactRead)
def read_project_artifact(
    artifact_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_READ))
):
    """Get project artifact by ID (All authenticated users can read)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read artifacts."
        )
    
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    return db_artifact

@router.get("/project/{project_id}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_READ))
):
    """Get all artifacts for a specific project (All authenticated users can read)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read artifacts."
        )
    
    # Check if project exists
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
        
    artifacts = project_artifact_crud.get_by_project_id(db, project_id=project_id)
    logger.info(f"User {current_user.username} ({current_user.get_roles()}) read {len(artifacts)} artifacts for project")
    return artifacts

@router.get("/version/{version_id}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_version(
    version_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_READ))
):
    """Get all artifacts based on a specific document version (All authenticated users can read)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read artifacts."
        )
    
    # Check if version exists
    db_version = document_version_crud.get(db, doc_version_id=version_id)
    if db_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document version not found"
        )
        
    return project_artifact_crud.get_by_version(db, version_id=version_id)

@router.get("/type/{artifact_type}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_type(
    artifact_type: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_READ))
):
    """Get artifacts by type (All authenticated users can read)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read artifacts."
        )
    
    return project_artifact_crud.get_by_artifact_type(db, artifact_type=artifact_type)

@router.get("/", response_model=List[ProjectArtifactRead])
def read_project_artifacts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_READ))
):
    """Get all project artifacts with pagination (All authenticated users can read)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read artifacts."
        )
    
    return project_artifact_crud.get_multi(db, skip=skip, limit=limit)

@router.put("/{artifact_id}", response_model=ProjectArtifactRead)
def update_project_artifact(
    artifact_id: uuid.UUID, 
    artifact: ProjectArtifactUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_UPDATE))
):
    """Update project artifact (Manager/Tester only)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only managers and testers can update artifacts."
        )
    
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    
    updated_artifact = project_artifact_crud.update(db=db, id=artifact_id, obj_in=artifact)
    logger.info(f"User {current_user.username} ({current_user.get_roles()}) updated artifact {artifact_id}")
    return updated_artifact

@router.delete("/{artifact_id}", response_model=ProjectArtifactRead)
def delete_project_artifact(
    artifact_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ARTIFACT_DELETE))
):
    """Delete project artifact (Manager only)"""
    # Check permissions
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.ARTIFACT_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only managers can delete artifacts."
        )
    
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    
    deleted_artifact = project_artifact_crud.remove(db=db, id=artifact_id)
    if deleted_artifact:
        logger.info(f"Manager {current_user.username} deleted artifact {artifact_id}")
    return deleted_artifact
    return project_artifact_crud.remove(db=db, id=artifact_id)
