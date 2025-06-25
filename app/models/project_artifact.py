# filepath: app/models/project_artifact.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .project import Project
    from .document_version import DocumentVersion
    from .user import User

class ProjectArtifact(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", nullable=False)
    based_on_version: uuid.UUID = Field(foreign_key="documentversion.id", nullable=False)
    artifact_type: str = Field(nullable=False)
    file_path: str = Field(nullable=False)
    deprecated: bool = Field(default=False, nullable=False)
    deprecated_reason: Optional[str] = None
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    
    # Relationships
    project: Optional["Project"] = Relationship(
        back_populates="artifacts",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.project_id]"}
    )
    
    based_on: Optional["DocumentVersion"] = Relationship(
        back_populates="artifacts",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.based_on_version]"}
    )
    
    creator: Optional["User"] = Relationship(
        back_populates="created_artifacts",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.created_by]"}
    )
    
    updater: Optional["User"] = Relationship(
        back_populates="updated_artifacts",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.updated_by]"}
    )
