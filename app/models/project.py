# filepath: app/models/project.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .document_version import DocumentVersion
    from .project_artifact import ProjectArtifact
    from .user import User
    from .chat import ChatSession

class Project(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    repo_path: Optional[str] = None
    current_version: Optional[uuid.UUID] = Field(default=None, foreign_key="documentversion.id", nullable=True)
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed name to avoid SQLAlchemy reserved word 'metadata'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    
    # Chats associated with this project
    chats: List["ChatSession"] = Relationship(back_populates="project")
    
    # Relationship with all document versions of this project
    document_versions: List["DocumentVersion"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.project_id]"}
    )
    
    # Relationship with the current active document version
    current_version_obj: Optional["DocumentVersion"] = Relationship(
        back_populates="current_for_projects",
        sa_relationship_kwargs={"foreign_keys": "[Project.current_version]"}
    )
    
    # Relationship with artifacts generated from this project
    artifacts: List["ProjectArtifact"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"foreign_keys": "[ProjectArtifact.project_id]"}
    )
    
    # Relationship with the user who created this project
    creator: Optional["User"] = Relationship(
        back_populates="created_projects",
        sa_relationship_kwargs={"foreign_keys": "[Project.created_by]"}
    )
    
    # Relationship with the user who last updated this project
    updater: Optional["User"] = Relationship(
        back_populates="updated_projects", 
        sa_relationship_kwargs={"foreign_keys": "[Project.updated_by]"}
    )
