from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional
import uuid

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_simple import ProjectCreateSimple
from app.schemas.document_version import DocumentVersionCreate
from app.crud.project_crud import project_crud
from app.crud.document_version_crud import document_version_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ProjectRead)
def create_project(
    project_simple: ProjectCreateSimple, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create new project with required name and optional meta_data and note fields.
    Authentication is required via JWT token.
    User IDs for created_by and updated_by are automatically set from the authenticated user.
    """
    # Check if project with the same name exists
    db_project = project_crud.get_by_name(db, name=project_simple.name)
    if db_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Project with this name already exists"
        )
    
    # Create project schema with user IDs from current user
    project_data = ProjectCreate(
        name=project_simple.name,
        meta_data=project_simple.meta_data,
        note=project_simple.note,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Create the project (filesystem structure will be created in the CRUD method)
    new_project = project_crud.create(db=db, project=project_data)
    
    # Create initial "v0" document version
    initial_version = DocumentVersionCreate(
        project_id=new_project.id,
        version_label="v0",
        is_current=True,
        note="Initial version",
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Create the document version
    doc_version = document_version_crud.create(db=db, doc_version=initial_version)
    
    # Update the project with the new version and get the refreshed project
    new_project = project_crud.update(
        db=db,
        project=ProjectUpdate(
            current_version=doc_version.id,
            updated_by=current_user.id
        ),
        project_id=new_project.id
    )
    
    return new_project

@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get project by ID"""
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    return db_project

@router.get("/", response_model=List[ProjectRead])
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects created by the current user with pagination.
    Authentication is required via JWT token.
    """
    projects = project_crud.get_by_user(
        db, 
        user_id=current_user.id,
        skip=skip, 
        limit=limit
    )
    return projects

@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: uuid.UUID, project: ProjectUpdate, db: Session = Depends(get_db)):
    """Update project"""
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    return project_crud.update(db=db, project=project, project_id=project_id)

@router.delete("/{project_id}", response_model=ProjectRead)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete project"""
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    return project_crud.delete(db=db, project_id=project_id)
