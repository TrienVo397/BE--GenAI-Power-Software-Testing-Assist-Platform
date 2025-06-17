from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
import uuid

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.crud.project_crud import project_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ProjectRead)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create new project"""
    db_project = project_crud.get_by_name(db, name=project.name)
    if db_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Project with this name already exists"
        )
    return project_crud.create(db=db, project=project)

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
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all projects with pagination"""
    projects = project_crud.get_multi(db, skip=skip, limit=limit)
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
