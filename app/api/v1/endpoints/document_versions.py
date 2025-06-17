from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid

from app.schemas.document_version import DocumentVersionCreate, DocumentVersionRead, DocumentVersionUpdate
from app.crud.document_version_crud import document_version_crud
from app.crud.project_crud import project_crud
from app.api.deps import get_db
from app.models.project import Project

router = APIRouter()

@router.post("/", response_model=DocumentVersionRead)
def create_document_version(doc_version: DocumentVersionCreate, db: Session = Depends(get_db)):
    """Create new document version"""
    # Verify project exists
    project = project_crud.get(db, project_id=doc_version.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
        
    # Create document version
    db_doc_version = document_version_crud.create(db=db, doc_version=doc_version)
    
    # If this is the current version, update the project's current_version reference
    if doc_version.is_current:
        project.current_version = db_doc_version.id
        db.add(project)
        db.commit()
        db.refresh(project)
        
    return db_doc_version

@router.get("/{doc_version_id}", response_model=DocumentVersionRead)
def read_document_version(doc_version_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get document version by ID"""
    db_doc_version = document_version_crud.get(db, doc_version_id=doc_version_id)
    if db_doc_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found"
        )
    return db_doc_version

@router.get("/project/{project_id}", response_model=List[DocumentVersionRead])
def read_document_versions_by_project(
    project_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Get all document versions for a project"""
    # Verify project exists
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
        
    versions = document_version_crud.get_by_project(
        db, project_id=project_id, skip=skip, limit=limit
    )
    return versions

@router.get("/project/{project_id}/current", response_model=DocumentVersionRead)
def get_current_document_version(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get current document version for a project"""
    # Verify project exists
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
        
    version = document_version_crud.get_current_version(db, project_id=project_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current version found for this project"
        )
    return version

@router.put("/{doc_version_id}", response_model=DocumentVersionRead)
def update_document_version(
    doc_version_id: uuid.UUID, doc_version: DocumentVersionUpdate, db: Session = Depends(get_db)
):
    """Update document version"""
    db_doc_version = document_version_crud.get(db, doc_version_id=doc_version_id)
    if db_doc_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found"
        )
    
    # Save project ID before updating
    project_id = db_doc_version.project_id
    
    # Update the document version
    updated_version = document_version_crud.update(
        db=db, doc_version=doc_version, doc_version_id=doc_version_id
    )
    
    # Handle current version status
    if hasattr(doc_version, "is_current") and doc_version.is_current:
        # Get the project and update its current_version
        project = project_crud.get(db, project_id=project_id)
        if project:
            project.current_version = doc_version_id
            db.add(project)
            db.commit()
            db.refresh(project)
    
    return updated_version

@router.delete("/{doc_version_id}", response_model=DocumentVersionRead)
def delete_document_version(doc_version_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete document version"""
    db_doc_version = document_version_crud.get(db, doc_version_id=doc_version_id)
    if db_doc_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found"
        )
    
    # Find any projects that have this as current version and update them
    projects = db.exec(select(Project).where(Project.current_version == doc_version_id)).all()
    for project in projects:
        project.current_version = None
        db.add(project)
    
    if projects:
        db.commit()
        
    return document_version_crud.delete(db=db, doc_version_id=doc_version_id)
