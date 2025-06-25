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
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ProjectArtifactRead)
def create_project_artifact(
    artifact: ProjectArtifactCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new project artifact"""
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
    
    return project_artifact_crud.create(db=db, obj_in=artifact)

@router.get("/{artifact_id}", response_model=ProjectArtifactRead)
def read_project_artifact(
    artifact_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project artifact by ID"""
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
    current_user: User = Depends(get_current_user)
):
    """Get all artifacts for a specific project"""
    # Check if project exists
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
        
    return project_artifact_crud.get_by_project_id(db, project_id=project_id)

@router.get("/version/{version_id}", response_model=List[ProjectArtifactRead])
def read_project_artifacts_by_version(
    version_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all artifacts based on a specific document version"""
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
    current_user: User = Depends(get_current_user)
):
    """Get artifacts by type"""
    return project_artifact_crud.get_by_artifact_type(db, artifact_type=artifact_type)

@router.get("/", response_model=List[ProjectArtifactRead])
def read_project_artifacts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all project artifacts with pagination"""
    return project_artifact_crud.get_multi(db, skip=skip, limit=limit)

@router.put("/{artifact_id}", response_model=ProjectArtifactRead)
def update_project_artifact(
    artifact_id: uuid.UUID, 
    artifact: ProjectArtifactUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project artifact"""
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    return project_artifact_crud.update(db=db, id=artifact_id, obj_in=artifact)

@router.delete("/{artifact_id}", response_model=ProjectArtifactRead)
def delete_project_artifact(
    artifact_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project artifact"""
    db_artifact = project_artifact_crud.get(db, id=artifact_id)
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project artifact not found"
        )
    return project_artifact_crud.remove(db=db, id=artifact_id)
