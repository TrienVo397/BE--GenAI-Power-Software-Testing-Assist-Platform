# filepath: app/models/project_member.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from enum import Enum
import uuid

if TYPE_CHECKING:
    from .project import Project
    from .user import User

class ProjectRole(str, Enum):
    """Roles a user can have within a specific project"""
    MANAGER = "manager"       # Can manage project content and members (full CRUD)
    TESTER = "tester"        # Can create and manage test artifacts (CREATE, READ, UPDATE)
    VIEWER = "viewer"        # Read-only access to project content

class ProjectMember(SQLModel, table=True):
    """
    Association table for project membership with role assignments.
    Maps users to projects with specific roles within that project.
    
    This allows users to have different roles in different projects:
    - User A could be a LEAD in Project 1 but a TESTER in Project 2
    - User B could be a VIEWER in Project 1 but a MANAGER in Project 3
    """
    
    # Composite primary key
    project_id: uuid.UUID = Field(foreign_key="project.id", primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    
    # Role within this specific project
    role: ProjectRole = Field(default=ProjectRole.VIEWER, nullable=False)
    
    # Membership management
    is_active: bool = Field(default=True, nullable=False)  # Can temporarily disable membership
    
    # Audit fields
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    added_by: Optional[uuid.UUID] = Field(foreign_key="user.id", default=None)  # Who added this user to the project
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by: Optional[uuid.UUID] = Field(foreign_key="user.id", default=None)  # Who last updated this membership
    
    # Relationships
    project: "Project" = Relationship(
        back_populates="members",
        sa_relationship_kwargs={"foreign_keys": "[ProjectMember.project_id]"}
    )
    
    user: "User" = Relationship(
        back_populates="project_memberships",
        sa_relationship_kwargs={"foreign_keys": "[ProjectMember.user_id]"}
    )
    
    # User who added this member (optional)
    added_by_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ProjectMember.added_by]"}
    )
    
    # User who last updated this membership (optional)
    updated_by_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ProjectMember.updated_by]"}
    )
    
    def can_manage_project(self) -> bool:
        """Check if this member can manage project settings"""
        return self.role == ProjectRole.MANAGER
    
    def can_manage_members(self) -> bool:
        """Check if this member can add/remove other members"""
        return self.role == ProjectRole.MANAGER
    
    def can_modify_content(self) -> bool:
        """Check if this member can modify project content"""
        return self.role in [ProjectRole.MANAGER, ProjectRole.TESTER]
    
    def can_create_artifacts(self) -> bool:
        """Check if this member can create test artifacts"""
        return self.role in [ProjectRole.MANAGER, ProjectRole.TESTER]
    
    def is_read_only(self) -> bool:
        """Check if this member has only read access"""
        return self.role == ProjectRole.VIEWER
