# filepath: app/schemas/admin.py
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

class AdminBase(BaseModel):
    admin_username: str
    admin_email: EmailStr
    full_name: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None

class AdminCreate(AdminBase):
    """Schema for creating a new admin - all admins have full access"""
    linked_user_id: Optional[uuid.UUID] = None  # Link to existing user account

class AdminUpdate(BaseModel):
    """Schema for updating admin information"""
    admin_username: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    linked_user_id: Optional[uuid.UUID] = None

class AdminRead(AdminBase):
    """Schema for reading admin information"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    linked_user_id: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(from_attributes=True)

class AdminSummary(BaseModel):
    """Minimal admin information for lists and references"""
    id: uuid.UUID
    admin_username: str
    admin_email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class AdminProfile(BaseModel):
    """Extended admin profile with permissions - all admins have full access"""
    id: uuid.UUID
    admin_username: str
    admin_email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None
    admin_roles: List[str]  # Always ["admin"] for simplified system
    permissions: List[str]  # Always ["all"] for full access
    is_active: bool
    is_super_admin: bool    # Always True for simplified system
    requires_2fa: bool      # Always False for simplified system
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    linked_user_id: Optional[uuid.UUID] = None

class AdminCredentialCreate(BaseModel):
    """Schema for creating admin credentials"""
    admin_id: uuid.UUID
    password: str

class AdminCredentialUpdate(BaseModel):
    """Schema for updating admin credentials"""
    password: Optional[str] = None

# Admin authentication schemas
class AdminLogin(BaseModel):
    """Admin login schema"""
    admin_username: str
    password: str

class AdminToken(BaseModel):
    """Admin authentication token"""
    access_token: str
    token_type: str
    admin_id: uuid.UUID
    admin_username: str
    permissions: List[str]  # Always ["all"] for full access
    expires_at: datetime

class AdminRegister(BaseModel):
    """Schema for initial admin registration - all admins have full access"""
    admin_username: str
    admin_email: EmailStr
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None
