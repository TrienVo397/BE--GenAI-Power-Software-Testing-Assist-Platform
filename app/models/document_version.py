from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .project import Project

class DocumentVersion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", nullable=False)
    version_label: str = Field(nullable=False)
    is_current: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_by: str = Field(nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_by: str = Field(nullable=False)
    
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
