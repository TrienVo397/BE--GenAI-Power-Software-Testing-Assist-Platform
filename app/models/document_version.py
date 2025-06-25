# filepath: app/models/document_version.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .project import Project
    from .project_artifact import ProjectArtifact
    from .user import User

class DocumentVersion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", nullable=False)
    version_label: str = Field(nullable=False)
    is_current: bool = Field(default=False, nullable=False)
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    
    # Relationship with the Project that owns this version
    project: Optional["Project"] = Relationship(
        back_populates="document_versions",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.project_id]"}
    )
    
    # Relationship with Projects that have this version as current
    current_for_projects: List["Project"] = Relationship(
        back_populates="current_version_obj",
        sa_relationship_kwargs={"foreign_keys": "[Project.current_version]"}
    )
    
    # Relationship with artifacts based on this version
    artifacts: List["ProjectArtifact"] = Relationship(
        back_populates="based_on", 
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.based_on_version]"}
    )
    
    # Relationship with the user who created this version
    creator: Optional["User"] = Relationship(
        back_populates="created_document_versions",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.created_by]"}
    )
    
    # Relationship with the user who last updated this version
    updater: Optional["User"] = Relationship(
        back_populates="updated_document_versions",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.updated_by]"}
    )
