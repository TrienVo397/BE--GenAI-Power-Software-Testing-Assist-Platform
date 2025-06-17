from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .document_version import DocumentVersion

class Project(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    repo_path: str
    current_version: Optional[uuid.UUID] = Field(default=None, foreign_key="documentversion.id", nullable=True)
    project_metadata: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_by: str = Field(nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_by: str = Field(nullable=False)
    
    # Relationship with all document versions of this project
    document_versions: List["DocumentVersion"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"foreign_keys": "[DocumentVersion.project_id]"}
