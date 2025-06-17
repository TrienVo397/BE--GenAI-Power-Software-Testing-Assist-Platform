from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

# Base Schema with common attributes
class ProjectBase(BaseModel):
    name: str
    repo_path: str
    project_metadata: Optional[str] = None

# Schema for creating a new project
class ProjectCreate(ProjectBase):
    created_by: str
    updated_by: str

# Schema for updating an existing project
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    repo_path: Optional[str] = None
    current_version: Optional[uuid.UUID] = None
    project_metadata: Optional[str] = None
    updated_by: str

# Schema for reading project data
class ProjectRead(ProjectBase):
    id: uuid.UUID
    current_version: Optional[uuid.UUID] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    
    model_config = ConfigDict(from_attributes=True)