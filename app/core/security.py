import asyncio
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from datetime import datetime, timedelta
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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Dependency to get the current user from JWT token."""
    from app.crud import user_crud
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise credentials_exception
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise credentials_exception
    return user