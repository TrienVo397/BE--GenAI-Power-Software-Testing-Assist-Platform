from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class DocumentVersionBase(BaseModel):
    project_id: uuid.UUID
    version_label: str
    is_current: bool = False

class DocumentVersionCreate(DocumentVersionBase):
    created_by: str
    updated_by: str

class DocumentVersionUpdate(BaseModel):
    version_label: Optional[str] = None
    is_current: Optional[bool] = None
    updated_by: str

class DocumentVersionRead(DocumentVersionBase):
    id: uuid.UUID
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    
    model_config = ConfigDict(from_attributes=True)
