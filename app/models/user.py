# filepath: app/models/user.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

if TYPE_CHECKING:
    from .credential import Credential
    from .project import Project
    from .document_version import DocumentVersion
    from .project_artifact import ProjectArtifact
    from .chat import ChatSession

class UserRole(str, Enum):
    """User roles for regular application users (non-admin)"""
    MANAGER = "manager"       # Project management capabilities
    TESTER = "tester"        # Standard testing operations
    VIEWER = "viewer"        # Read-only access

class User(SQLModel, table=True):
    """
    Regular application user model
    Separated from admin functionality for better security
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    full_name: Optional[str] = None
    notes: Optional[str] = None
    
    # User role system - stored as JSON array for multiple roles
    roles: str = Field(default='["viewer"]', nullable=False)  # JSON string: ["tester", "manager"]
    
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
    
    # Helper methods for role management
    def get_roles(self) -> List[UserRole]:
        """Parse roles from JSON string to list of UserRole enums"""
        try:
            role_strings = json.loads(self.roles)
            return [UserRole(role) for role in role_strings if role in [r.value for r in UserRole]]
        except (json.JSONDecodeError, ValueError):
            return [UserRole.VIEWER]
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role"""
        return role in self.get_roles()
    
    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles"""
        user_roles = self.get_roles()
        return any(role in user_roles for role in roles)
    
    def add_role(self, role: UserRole) -> None:
        """Add a role to the user"""
        current_roles = self.get_roles()
        if role not in current_roles:
            current_roles.append(role)
            self.roles = json.dumps([r.value for r in current_roles])
    
    def remove_role(self, role: UserRole) -> None:
        """Remove a role from the user"""
        current_roles = [r for r in self.get_roles() if r != role]
        self.roles = json.dumps([r.value for r in current_roles])
    
    def is_manager(self) -> bool:
        """Check if user has manager role"""
        return self.has_role(UserRole.MANAGER)
    
    def can_manage_projects(self) -> bool:
        """Check if user can manage projects"""
        return self.has_role(UserRole.MANAGER) or self.has_role(UserRole.TESTER)
    
    def can_create_artifacts(self) -> bool:
        """Check if user can create test artifacts"""
        return self.has_role(UserRole.MANAGER) or self.has_role(UserRole.TESTER)
    
    def is_read_only(self) -> bool:
        """Check if user has only read access"""
        user_roles = self.get_roles()
        return len(user_roles) == 1 and UserRole.VIEWER in user_roles
