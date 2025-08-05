from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

# Base Schema with common attributes
class ProjectBase(BaseModel):
    name: str
    meta_data: Optional[str] = None  # Changed from project_metadata to match model/ER diagram 
    note: Optional[str] = None
    repo_path: Optional[str] = None
    start_date: Optional[datetime] = None  # Project start date
    end_date: Optional[datetime] = None  # Project end date

# Schema for creating a new project
class ProjectCreate(ProjectBase):
    created_by: uuid.UUID
    updated_by: uuid.UUID
    
# Schema for creating a simple project (without repo_path)
class ProjectCreateSimple(BaseModel):
    name: str
    meta_data: Optional[str] = None
    note: Optional[str] = None
    start_date: Optional[datetime] = None  # Project start date
    end_date: Optional[datetime] = None  # Project end date

# Schema for updating an existing project
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    current_version: Optional[uuid.UUID] = None
    meta_data: Optional[str] = None  # Changed from project_metadata to match model/ER diagram
    note: Optional[str] = None
    start_date: Optional[datetime] = None  # Project start date
    end_date: Optional[datetime] = None  # Project end date

# Schema for reading project data
class ProjectRead(ProjectBase):
    id: uuid.UUID
    current_version: Optional[uuid.UUID] = None
    created_at: datetime
    created_by: uuid.UUID
    updated_at: datetime
    updated_by: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)