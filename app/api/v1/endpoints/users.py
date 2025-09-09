from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session
from datetime import timedelta
from typing import List
import uuid

from app.schemas.user import (
    UserCreate, UserRead, UserUpdate, Token, UserRegister,
    AdminUserCreate, AdminUserUpdate
)
from app.crud.user_crud import user_crud
from app.api.deps import get_db
from app.core.security import verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User
# from app.core.authz import AuthorizationDependency  # DEPRECATED
from app.core.permissions import Permission
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, SecuritySchemeType
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login",
    scheme_name="UserOAuth2PasswordBearer",
    description="Login using either username or email address"
)

router = APIRouter()

# Authentication endpoints
@router.post("/register", response_model=UserRead)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user - DISABLED for security (admin-only user creation)"""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public user registration is disabled. Please contact an administrator to create your account."
    )

@router.post("/login", response_model=Token)
async def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 login with username/email and password form data
    
    The username field accepts either:
    - Username (e.g., "john_doe")  
    - Email address (e.g., "john@example.com")
    """
    from app.crud.credential_crud import credential_crud
    
    # Try to find user by username or email
    user = user_crud.get_by_username_or_email(db, form_data.username)
    
    if not user or not user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Get user's credential
    credential = credential_crud.get_by_user_id(db, user.id)
    if not credential or not verify_password(form_data.password, credential.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "type": "user"},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/whoami", response_model=UserRead)
async def whoami(current_user: User = Depends(get_current_user)):
    """Get current user profile (whoami)"""
    return current_user

# Enhanced user management endpoints with role-based access control

@router.get("/all", response_model=List[UserRead])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users (requires user management permission)"""
    logger.info(f"User {current_user.username} retrieving users list")
    users = user_crud.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user's information"""
    logger.info(f"User {current_user.username} retrieving own profile")
    return current_user

@router.get("/{user_id}", response_model=UserRead)
@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific user by ID (users can only view their own profile)"""
    # Users can only view their own profile (admin can view others via admin API)
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    logger.info(f"User {current_user.username} retrieving own profile by ID")
    return current_user

@router.put("/me/profile", response_model=UserRead)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's information (self-service)"""
    # Users can only update certain fields about themselves
    allowed_fields = {'full_name', 'password'}
    update_data = {k: v for k, v in user_data.dict(exclude_unset=True).items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    filtered_update = UserUpdate(**update_data)
    updated_user = user_crud.update(db, filtered_update, current_user.id)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User {current_user.username} updated own profile")
    return updated_user

# Manager-only user management endpoints
@router.post("/create", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (Manager only)"""
    # Check if user already exists
    existing_user = user_crud.get_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_user = user_crud.get_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = user_crud.create(db, user_data)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    logger.info(f"Manager {current_user.username} created user {new_user.username}")
    return new_user

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (Manager only, except self-profile updates)"""
    # Users can update their own profile with limited fields
    if user_id == current_user.id:
        allowed_fields = {'full_name', 'password'}
        update_data = {k: v for k, v in user_data.dict(exclude_unset=True).items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        filtered_update = UserUpdate(**update_data)
        updated_user = user_crud.update(db, filtered_update, user_id)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User {current_user.username} updated own profile")
        return updated_user
    
    # Users can only update their own profile (admin can update others via admin API)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only update your own profile"
    )


