# filepath: app/schemas/project_artifact.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class ProjectArtifactBase(BaseModel):
    project_id: uuid.UUID
    based_on_version: uuid.UUID
    artifact_type: str
    file_path: str
    deprecated: bool = False
    deprecated_reason: Optional[str] = None
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'

class ProjectArtifactCreate(ProjectArtifactBase):
    created_by: uuid.UUID
    updated_by: uuid.UUID

class ProjectArtifactUpdate(BaseModel):
    artifact_type: Optional[str] = None
    file_path: Optional[str] = None
    deprecated: Optional[bool] = None
    deprecated_reason: Optional[str] = None
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'
    updated_by: uuid.UUID

class ProjectArtifactRead(ProjectArtifactBase):
    id: uuid.UUID
    created_at: datetime
    created_by: uuid.UUID
    updated_at: datetime
    updated_by: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
