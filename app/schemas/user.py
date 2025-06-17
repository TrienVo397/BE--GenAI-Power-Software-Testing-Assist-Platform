from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserRead(UserBase):
    id: int
    full_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
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
    full_name: str = None

class UserInDB(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)