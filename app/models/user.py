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

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    full_name: Optional[str] = None
    notes: Optional[str] = None
    roles: Optional[str] = None  # Stored as JSON string, e.g. '["admin", "user"]'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    credential: Optional["Credential"] = Relationship(back_populates="user")
    
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
    