from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
import uuid
import re

class DocumentVersionBase(BaseModel):
    project_id: uuid.UUID
    version_label: str
    is_current: bool = False
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'
    
    @field_validator("version_label")
    @classmethod
    def validate_version_label(cls, v: str) -> str:
        pattern = r'^v\d+(\.\d+)?(\.\d+)?$'
        if not re.match(pattern, v):
            raise ValueError("Version label must be in format vX, vX.X, or vX.X.X (e.g., v1, v1.2, v1.2.3)")
        return v

class DocumentVersionCreate(DocumentVersionBase):
    created_by: uuid.UUID
    updated_by: uuid.UUID

class DocumentVersionUpdate(BaseModel):
    version_label: Optional[str] = None
    is_current: Optional[bool] = None
    note: Optional[str] = None
    meta_data: Optional[str] = None  # Changed to avoid SQLAlchemy reserved word 'metadata'
    
    @field_validator("version_label")
    @classmethod
    def validate_version_label(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        pattern = r'^v\d+(\.\d+)?(\.\d+)?$'
        if not re.match(pattern, v):
            raise ValueError("Version label must be in format vX, vX.X, or vX.X.X (e.g., v1, v1.2, v1.2.3)")
        return v

class DocumentVersionRead(DocumentVersionBase):
    id: uuid.UUID
    created_at: datetime
    created_by: uuid.UUID
    updated_at: datetime
    updated_by: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
