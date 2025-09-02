from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional
import uuid

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectCreateSimple
from app.schemas.document_version import DocumentVersionCreate
from app.schemas.project_artifact import ProjectArtifactCreate
from app.schemas.project_member import ProjectMemberCreate
from app.crud.project_crud import project_crud
from app.crud.document_version_crud import document_version_crud
from app.crud.project_artifact_crud import project_artifact_crud
from app.crud.project_member_crud import project_member_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.core.permissions import Permission, has_project_permission
from app.models.user import User
from app.models.project_member import ProjectRole
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ProjectRead)
def create_project(
    project_simple: ProjectCreateSimple, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create new project (Manager/Tester only)
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
        start_date=project_simple.start_date,  # Include start_date
        end_date=project_simple.end_date,  # Include end_date
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Create the project (filesystem structure will be created in the CRUD method)
    new_project = project_crud.create(db=db, project=project_data)
    
    # Make the creator a MANAGER of the project
    creator_membership = ProjectMemberCreate(
        user_id=current_user.id,
        role=ProjectRole.MANAGER
    )
    project_member_crud.add_member(db, new_project.id, creator_membership, current_user.id)
    
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
    doc_version = document_version_crud.create(db=db, doc_version=initial_version, current_user=current_user)
    
    # Create default project artifacts
    checklist_artifact = ProjectArtifactCreate(
        project_id=new_project.id,
        based_on_version=doc_version.id,
        artifact_type="checklist",
        file_path="artifacts/checklist.md",
        note="Initial checklist template",
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    testcases_artifact = ProjectArtifactCreate(
        project_id=new_project.id,
        based_on_version=doc_version.id,
        artifact_type="testcases",
        file_path="artifacts/testcase.md",
        note="Initial test cases template",
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    requirement_artifact = ProjectArtifactCreate(
        project_id=new_project.id,
        based_on_version=doc_version.id,
        artifact_type="requirement",
        file_path="artifacts/requirement.md",
        note="Initial requirement template",
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Create the artifacts
    project_artifact_crud.create(db=db, obj_in=checklist_artifact)
    project_artifact_crud.create(db=db, obj_in=testcases_artifact)
    project_artifact_crud.create(db=db, obj_in=requirement_artifact)
    
    # Update the project with the new version and get the refreshed project
    new_project = project_crud.update(
        db=db,
        project=ProjectUpdate(
            current_version=doc_version.id
        ),
        project_id=new_project.id,
        user_id=current_user.id
    )
    
    return new_project

@router.get("/{project_id}", response_model=ProjectRead)
def read_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project by ID (All project members can read)"""
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    
    # Check if user is a member of this project
    user_project_role = current_user.get_project_role(project_id)
    if user_project_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view this project"
        )
    
    logger.info(f"User {current_user.username} ({user_project_role}) read project {db_project.name}")
    return db_project

@router.get("/", response_model=List[ProjectRead])
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects where the current user is a member with pagination
    Only shows projects where user has been assigned a role (MANAGER, TESTER, or VIEWER)
    Authentication is required via JWT token.
    """
    projects = project_crud.get_by_user_membership(
        db, 
        user_id=current_user.id,
        skip=skip, 
        limit=limit
    )
    
    logger.info(f"User {current_user.username} (project member) found {len(projects)} accessible projects")
    return projects

@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID, 
    project: ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project (Manager/Tester only)"""
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    
    # Check if user can modify project content
    if not current_user.can_modify_project_content(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers and testers can update projects"
        )
    
    updated_project = project_crud.update(db=db, project=project, project_id=project_id, user_id=current_user.id)
    if updated_project:
        user_role = current_user.get_project_role(project_id)
        logger.info(f"User {current_user.username} ({user_role}) updated project {updated_project.name}")
    return updated_project

@router.delete("/{project_id}", response_model=ProjectRead)
def delete_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project (Manager only)"""
    db_project = project_crud.get(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found"
        )
    
    # Check if user can manage project (only managers can delete)
    if not current_user.can_manage_project_members(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers can delete projects"
        )
    
    deleted_project = project_crud.delete(db=db, project_id=project_id)
    if deleted_project:
        logger.info(f"Manager {current_user.username} deleted project {deleted_project.name}")
    return deleted_project
