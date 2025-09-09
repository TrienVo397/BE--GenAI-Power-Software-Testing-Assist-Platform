import asyncio
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.api.deps import get_db

from sqlmodel import Session
from app.core.config import settings
from app.crud import user_crud

# Security settings
SECRET_KEY = settings.secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expires_minutes

# Password hashing
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY.get_secret_value(), algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY.get_secret_value(), algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}
    
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login",
    scheme_name="UserOAuth2PasswordBearer"
)

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current user from JWT token.
    Also accepts admin tokens and creates a virtual user object for admins.
    """
    from app.crud import user_crud
    from app.crud.admin_crud import admin_crud
    from app.models.user import User
    import uuid
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    user_id = payload.get("sub") if payload else None
    token_type = payload.get("type", "user")  # Default to user if no type specified
    
    if not user_id:
        raise credentials_exception
    
    try:
        user_uuid = uuid.UUID(user_id)
        
        # Check if this is an admin token
        if token_type == "admin":
            # Get admin and create virtual user object
            admin = admin_crud.get(db, user_uuid)
            if not admin or not admin.is_active:
                raise credentials_exception
            
            # Create a virtual user object from admin data
            virtual_user = User(
                id=admin.id,
                username=admin.admin_username,
                email=admin.admin_email,
                full_name=admin.full_name,
                is_active=admin.is_active,
                is_verified=True,  # Admins are always verified
                notes=f"Virtual user for admin: {admin.admin_username}"
            )
            return virtual_user
        else:
            # Normal user token
            user = user_crud.get(db, user_id=user_uuid)
        if not user:
            raise credentials_exception
        return user
    except (ValueError, TypeError):
        raise credentials_exception