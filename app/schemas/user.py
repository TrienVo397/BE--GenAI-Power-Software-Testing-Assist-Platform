from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    notes: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    notes: Optional[str] = None
    roles: Optional[str] = None  # JSON string for roles
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserRead(UserBase):
    id: uuid.UUID
    roles: str  # JSON string of roles
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Admin-specific schemas for user management
class AdminUserCreate(UserBase):
    """Admin schema for creating users with role assignment"""
    password: str
    initial_roles: Optional[List[str]] = ["viewer"]  # List of role strings
    is_active: Optional[bool] = True

class AdminUserUpdate(BaseModel):
    """Admin schema for updating users with full control"""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    notes: Optional[str] = None
    roles: Optional[List[str]] = None  # List of role strings
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserRoleUpdate(BaseModel):
    """Schema specifically for updating user roles"""
    roles: List[str]  # List of role strings (required)

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    notes: Optional[str] = None

class UserInDB(UserBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)