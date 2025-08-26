# filepath: app/api/v1/endpoints/project_members.py
"""
API endpoints for project membership management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
import uuid
import logging

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project_member import ProjectRole
from app.schemas.project_member import (
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberRead,
    ProjectMembersResponse, UserProjectsResponse, ProjectMemberBatch,
    RolePermissionsInfo, AvailableRolesResponse
)
from app.crud.project_member_crud import project_member_crud
from app.crud.project_crud import project_crud
from app.crud.user_crud import user_crud

logger = logging.getLogger(__name__)

router = APIRouter()

# Project member management endpoints

@router.post("/projects/{project_id}/members", response_model=ProjectMemberRead)
async def add_project_member(
    project_id: uuid.UUID,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a user to a project with a specific role"""
    
    # Verify project exists
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user exists
    user = user_crud.get(db, member_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if current user can manage this project
    # User must be a MANAGER in this project to add members
    if not current_user.can_manage_project_members(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers can add members"
        )
    
    # Add the member
    member = project_member_crud.add_member(db, project_id, member_data, current_user.id)
    
    logger.info(f"User {current_user.username} added user {user.username} to project {project.name} with role {member_data.role}")
    return member

@router.get("/projects/{project_id}/members", response_model=ProjectMembersResponse)
async def get_project_members(
    project_id: uuid.UUID,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all members of a project"""
    
    # Verify project exists
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to this project
    if not current_user.is_project_member(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view project members"
        )
    
    # Get project members
    members = project_member_crud.get_project_members(db, project_id, active_only)
    
    # Enrich with user information
    member_reads = []
    for member in members:
        user = user_crud.get(db, member.user_id)
        member_read = ProjectMemberRead(
            project_id=member.project_id,
            user_id=member.user_id,
            role=member.role,
            is_active=member.is_active,
            joined_at=member.joined_at,
            added_by=member.added_by,
            updated_at=member.updated_at,
            updated_by=member.updated_by,
            user_username=user.username if user else None,
            user_email=user.email if user else None,
            user_full_name=user.full_name if user else None,
            project_name=project.name
        )
        member_reads.append(member_read)
    
    return ProjectMembersResponse(
        project_id=project_id,
        project_name=project.name,
        total_members=len(member_reads),
        members=member_reads
    )

@router.get("/users/{user_id}/projects", response_model=UserProjectsResponse)
async def get_user_project_memberships(
    user_id: uuid.UUID,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all project memberships for a user (users can only see their own)"""
    
    # Users can only view their own project memberships
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own project memberships"
        )
    
    # Verify user exists
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user memberships
    memberships = project_member_crud.get_user_memberships(db, user_id, active_only)
    
    # Enrich with project information
    membership_reads = []
    for membership in memberships:
        project = project_crud.get(db, membership.project_id)
        member_read = ProjectMemberRead(
            project_id=membership.project_id,
            user_id=membership.user_id,
            role=membership.role,
            is_active=membership.is_active,
            joined_at=membership.joined_at,
            added_by=membership.added_by,
            updated_at=membership.updated_at,
            updated_by=membership.updated_by,
            user_username=user.username,
            user_email=user.email,
            user_full_name=user.full_name,
            project_name=project.name if project else None
        )
        membership_reads.append(member_read)
    
    return UserProjectsResponse(
        user_id=user_id,
        user_username=user.username,
        total_projects=len(membership_reads),
        memberships=membership_reads
    )

@router.put("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberRead)
async def update_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    update_data: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a user's role or status in a project"""
    
    # Verify project exists
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify membership exists
    membership = project_member_crud.get_membership(db, project_id, user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )
    
    # Check permissions
    if not current_user.can_manage_project_members(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers can update member roles"
        )
    
    # Update membership
    updated_member = project_member_crud.update_membership(
        db, project_id, user_id, update_data, current_user.id
    )
    
    user = user_crud.get(db, user_id)
    if user:
        logger.info(f"User {current_user.username} updated membership for {user.username} in project {project.name}")
    
    return updated_member

@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a user from a project"""
    
    # Verify project exists
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify membership exists
    membership = project_member_crud.get_membership(db, project_id, user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )
    
    # Check permissions
    if not current_user.can_manage_project_members(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers can remove members"
        )
    
    # Remove member
    success = project_member_crud.remove_member(db, project_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member from project"
        )
    
    user = user_crud.get(db, user_id)
    if user:
        logger.info(f"User {current_user.username} removed {user.username} from project {project.name}")
    
    return {"message": "Member removed successfully"}

@router.post("/projects/{project_id}/members/batch", response_model=List[ProjectMemberRead])
async def add_multiple_project_members(
    project_id: uuid.UUID,
    batch_data: ProjectMemberBatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add multiple users to a project at once"""
    
    # Verify project exists
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    if not current_user.can_manage_project_members(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project managers can add members"
        )
    
    # Add multiple members
    members = project_member_crud.add_multiple_members(
        db, project_id, batch_data.user_roles, current_user.id
    )
    
    logger.info(f"User {current_user.username} added {len(members)} members to project {project.name}")
    return members

# Role information endpoints

@router.get("/project-roles", response_model=AvailableRolesResponse)
async def get_available_project_roles(
    current_user: User = Depends(get_current_user)
):
    """Get information about available project roles and their permissions"""
    
    roles_info = []
    for role in ProjectRole:
        # Create a temporary ProjectMember to check permissions
        from app.models.project_member import ProjectMember
        temp_member = ProjectMember(
            project_id=uuid.uuid4(),  # Dummy UUID
            user_id=uuid.uuid4(),     # Dummy UUID
            role=role
        )
        
        role_info = RolePermissionsInfo(
            role=role,
            can_manage_project=temp_member.can_manage_project(),
            can_manage_members=temp_member.can_manage_members(),
            can_modify_content=temp_member.can_modify_content(),
            can_create_artifacts=temp_member.can_create_artifacts(),
            is_read_only=temp_member.is_read_only()
        )
        roles_info.append(role_info)
    
    return AvailableRolesResponse(roles=roles_info)
