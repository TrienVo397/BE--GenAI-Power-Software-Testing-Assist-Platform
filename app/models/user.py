# filepath: app/models/user.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .credential import Credential
    from .project import Project
    from .document_version import DocumentVersion
    from .project_artifact import ProjectArtifact
    from .chat import ChatSession
    from .project_member import ProjectMember, ProjectRole

class User(SQLModel, table=True):
    """
    Regular application user model - roles are managed at project level
    Users have no global roles, only project-specific roles via ProjectMember
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    full_name: Optional[str] = None
    notes: Optional[str] = None
    
    # Status management
    is_active: bool = Field(default=True, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    last_login: Optional[datetime] = None
    
    # Relationships
    credential: Optional["Credential"] = Relationship(back_populates="user")
    
    # Chats
    chats: List["ChatSession"] = Relationship(back_populates="user")
    
    # Projects created by this user
    created_projects: List["Project"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Project.created_by]"}
    )
    
    # Projects updated by this user
    updated_projects: List["Project"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "[Project.updated_by]"}
    )
    
    # Document versions created by this user
    created_document_versions: List["DocumentVersion"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.created_by]"}
    )
    
    # Document versions updated by this user
    updated_document_versions: List["DocumentVersion"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.updated_by]"}
    )
    
    # Project artifacts created by this user
    created_artifacts: List["ProjectArtifact"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.created_by]"}
    )
    
    # Project artifacts updated by this user
    updated_artifacts: List["ProjectArtifact"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.updated_by]"}
    )
    
    # Project memberships - projects this user is a member of with specific roles
    project_memberships: List["ProjectMember"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ProjectMember.user_id]"}
    )
    
    # Project-specific helper methods (no global roles)
    def get_project_role(self, project_id) -> Optional["ProjectRole"]:
        """Get user's role in a specific project"""
        from .project_member import ProjectRole
        for membership in self.project_memberships:
            if membership.project_id == project_id and membership.is_active:
                return membership.role
        return None
    
    def is_project_member(self, project_id) -> bool:
        """Check if user is an active member of a project"""
        return any(
            membership.project_id == project_id and membership.is_active
            for membership in self.project_memberships
        )
    
    def can_manage_project_members(self, project_id) -> bool:
        """Check if user can manage members of a specific project"""
        for membership in self.project_memberships:
            if membership.project_id == project_id and membership.is_active:
                return membership.can_manage_members()
        return False
    
    def can_modify_project_content(self, project_id) -> bool:
        """Check if user can modify content in a specific project"""
        for membership in self.project_memberships:
            if membership.project_id == project_id and membership.is_active:
                return membership.can_modify_content()
        return False
    
    def can_create_project_artifacts(self, project_id) -> bool:
        """Check if user can create artifacts in a specific project"""
        for membership in self.project_memberships:
            if membership.project_id == project_id and membership.is_active:
                return membership.can_create_artifacts()
        return False
    
    def is_project_read_only(self, project_id) -> bool:
        """Check if user has only read access to a specific project"""
        for membership in self.project_memberships:
            if membership.project_id == project_id and membership.is_active:
                return membership.is_read_only()
        return True  # No membership = read-only (or no access)
    
    def get_managed_projects(self) -> List:
        """Get all projects where user has manager role"""
        from .project_member import ProjectRole
        return [
            membership.project_id for membership in self.project_memberships
            if membership.is_active and membership.role == ProjectRole.MANAGER
        ]
