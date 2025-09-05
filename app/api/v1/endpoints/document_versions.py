from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid

from app.schemas.document_version import DocumentVersionCreate, DocumentVersionRead, DocumentVersionUpdate
from app.crud.document_version_crud import document_version_crud
from app.crud.project_crud import project_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.core.permissions import Permission
# from app.core.authz import require_permissions  # DEPRECATED
from app.models.user import User
from app.models.project import Project
from app.utils.project_fs import ProjectFSError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=DocumentVersionRead)
async def create_document_version(
    doc_version: DocumentVersionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new document version (Manager/Tester only)"""
    # Verify project exists
    project = project_crud.get(db, project_id=doc_version.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user can modify project content (Manager/Tester)
    if not current_user.can_modify_project_content(doc_version.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers and testers can create document versions"
        )
        
    # Create document version - validation happens in the CRUD method
    try:
        db_doc_version = document_version_crud.create(db=db, doc_version=doc_version, current_user=current_user)
        logger.info(f"User {current_user.username}  created document version {doc_version.version_label}")
        return db_doc_version
    except HTTPException:
        # Re-raise HTTP exceptions directly
        raise
    except Exception as e:
        # Handle any other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document version: {str(e)}"
        )

@router.get("/{doc_version_id}", response_model=DocumentVersionRead)
async def read_document_version(
    doc_version_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document version by ID (All authenticated users can read)"""
    # Project-specific permission check removed - add back if needed
    
    db_doc_version = document_version_crud.get(db, doc_version_id=doc_version_id)
    if db_doc_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found"
        )
    return db_doc_version

@router.get("/project/{project_id}", response_model=List[DocumentVersionRead])
async def read_document_versions_by_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all document versions for a project (All authenticated users can read)"""
    # Project-specific permission check removed - add back if needed
    
    # Verify project exists
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
        
    versions = document_version_crud.get_by_project(
        db, project_id=project_id
    )
    logger.info(f"User {current_user.username}  read {len(versions)} document versions")
    return versions

@router.get("/project/{project_id}/current", response_model=DocumentVersionRead)
async def get_current_document_version(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current document version for a project (All authenticated users can read)"""
    # Project-specific permission check removed - add back if needed
    
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
async def update_document_version(
    doc_version_id: uuid.UUID, 
    doc_version: DocumentVersionUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document version (Manager/Tester only)"""
    # Project-specific permission check removed - add back if needed
    
    db_doc_version = document_version_crud.get(db, doc_version_id=doc_version_id)
    if db_doc_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found"
        )
    # Update the document version
    # Note: document_version_crud.update will handle making this the current version if necessary
    updated_version = document_version_crud.update(
        db=db, doc_version=doc_version, doc_version_id=doc_version_id, current_user=current_user
    )
    if not updated_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found"
        )
    
    logger.info(f"User {current_user.username}  updated document version {doc_version_id}")
    return updated_version

@router.delete("/{doc_version_id}", response_model=DocumentVersionRead)
async def delete_document_version(
    doc_version_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document version (Manager only)"""
    # Project-specific permission check removed - add back if needed
    
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
    
    deleted_version = document_version_crud.delete(db=db, doc_version_id=doc_version_id, current_user=current_user)
    logger.info(f"Manager {current_user.username} deleted document version {doc_version_id}")
    return deleted_version

