from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class DocumentVersionBase(BaseModel):
    project_id: uuid.UUID
    version_label: str
    is_current: bool = False
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'

class DocumentVersionCreate(DocumentVersionBase):
    created_by: uuid.UUID
    updated_by: uuid.UUID

class DocumentVersionUpdate(BaseModel):
    version_label: Optional[str] = None
    is_current: Optional[bool] = None
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'
    updated_by: uuid.UUID

class DocumentVersionRead(DocumentVersionBase):
    id: uuid.UUID
    created_at: datetime
    created_by: uuid.UUID
    updated_at: datetime
    updated_by: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
