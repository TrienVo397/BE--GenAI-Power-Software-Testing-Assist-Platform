# filepath: app/models/admin.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .user import User

class Admin(SQLModel, table=True):
    """
    Admin model for system administrators with full access privileges
    All authenticated admins have access to all admin APIs
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Admin credentials
    admin_username: str = Field(index=True, unique=True, nullable=False)
    admin_email: str = Field(index=True, unique=True, nullable=False)
    
    # Admin profile
    full_name: Optional[str] = None
    department: Optional[str] = None  # IT, Security, etc.
    notes: Optional[str] = None
    
    # Security settings
    is_active: bool = Field(default=True, nullable=False)
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    last_login: Optional[datetime] = None
    
    # Admin who created this admin (for audit trail)
    created_by: Optional[uuid.UUID] = Field(foreign_key="admin.id", nullable=True)
    
    # Admin relationships
    creator: Optional["Admin"] = Relationship(
        back_populates="created_admins",
        sa_relationship_kwargs={"remote_side": "Admin.id"}
    )
    
    created_admins: list["Admin"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Admin.created_by]"}
    )
    
    # Link to regular user account (optional - admin might not have a regular user account)
    linked_user_id: Optional[uuid.UUID] = Field(foreign_key="user.id", nullable=True)
    linked_user: Optional["User"] = Relationship()
    
    # Simple helper methods
    def is_admin(self) -> bool:
        """Check if this is an active admin - all active admins have full access"""
        return self.is_active
