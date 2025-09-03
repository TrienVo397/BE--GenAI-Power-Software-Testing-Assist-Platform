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
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Admin-specific schemas for user management
class AdminUserCreate(UserBase):
    """Admin schema for creating users - no global roles"""
    password: str
    is_active: Optional[bool] = True

class AdminUserUpdate(BaseModel):
    """Admin schema for updating users"""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    """User login schema - accepts username or email"""
    username: str  # OAuth2 standard field name, but accepts username or email
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe or john@example.com",
                "password": "your_password"
            },
            "description": "OAuth2 login form. The 'username' field accepts either username or email address."
        }
    )

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    notes: Optional[str] = None

class UserInDB(UserBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)