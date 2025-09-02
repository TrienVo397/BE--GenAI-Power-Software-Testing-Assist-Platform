# filepath: app/schemas/project_member.py
"""
Pydantic schemas for project membership management
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.project_member import ProjectRole

# Base schemas
class ProjectMemberBase(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectRole
    is_active: bool = True

class ProjectMemberCreate(BaseModel):
    """Schema for adding a user to a project with a specific role"""
    user_id: uuid.UUID
    role: ProjectRole = ProjectRole.VIEWER
    is_active: bool = True

class ProjectMemberUpdate(BaseModel):
    """Schema for updating a user's role in a project"""
    role: Optional[ProjectRole] = None
    is_active: Optional[bool] = None

class ProjectMemberRead(ProjectMemberBase):
    """Schema for reading project member information"""
    joined_at: datetime
    added_by: Optional[uuid.UUID] = None
    updated_at: datetime
    updated_by: Optional[uuid.UUID] = None
    
    # Include user and project basic info for convenience
    user_username: Optional[str] = None
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    project_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProjectMemberBatch(BaseModel):
    """Schema for adding multiple users to a project at once"""
    user_roles: List[ProjectMemberCreate]

# Response schemas
class ProjectMembersResponse(BaseModel):
    """Schema for listing all members of a project"""
    project_id: uuid.UUID
    project_name: str
    total_members: int
    members: List[ProjectMemberRead]

class UserProjectsResponse(BaseModel):
    """Schema for listing all projects a user is a member of"""
    user_id: uuid.UUID
    user_username: str
    total_projects: int
    memberships: List[ProjectMemberRead]

# Role management schemas
class RolePermissionsInfo(BaseModel):
    """Information about what each project role can do"""
    role: ProjectRole
    can_manage_project: bool
    can_manage_members: bool
    can_modify_content: bool
    can_create_artifacts: bool
    is_read_only: bool

class AvailableRolesResponse(BaseModel):
    """Schema for available project roles and their permissions"""
    roles: List[RolePermissionsInfo]
