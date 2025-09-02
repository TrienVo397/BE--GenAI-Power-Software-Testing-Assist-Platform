# filepath: app/models/admin_credential.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .admin import Admin

class AdminCredential(SQLModel, table=True):
    """
    Admin credentials - simplified to match user credential structure
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Foreign key to admin
    admin_id: uuid.UUID = Field(foreign_key="admin.id", unique=True, nullable=False)
    
    # Credential fields
    hashed_password: str = Field(nullable=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship back to admin
    admin: Optional["Admin"] = Relationship()
