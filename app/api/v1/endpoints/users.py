from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session
from datetime import timedelta
from typing import List
import uuid

from app.schemas.user import (
    UserCreate, UserRead, UserUpdate, Token, UserRegister,
    AdminUserCreate, AdminUserUpdate, UserRoleUpdate
)
from app.crud.user_crud import user_crud
from app.api.deps import get_db
from app.core.security import verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User, UserRole
from app.core.authz import require_permissions
from app.core.permissions import Permission
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, SecuritySchemeType
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login",
    scheme_name="UserOAuth2PasswordBearer"
)

router = APIRouter()

# Authentication endpoints
@router.post("/register", response_model=UserRead)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user - DISABLED for security (admin-only user creation)"""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public user registration is disabled. Please contact an administrator to create your account."
    )

@router.post("/login", response_model=Token)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 login with username and password form data"""
    from app.crud.credential_crud import credential_crud
    
    user = user_crud.get_by_username(db, form_data.username)
    if not user or not user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Get user's credential
    credential = credential_crud.get_by_user_id(db, user.id)
    if not credential or not verify_password(form_data.password, credential.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
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
    current_user: User = Depends(require_permissions(Permission.USER_READ)),
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
    """Get specific user by ID (requires user view permission or self)"""
    # Users can always view their own profile
    if user_id == current_user.id:
        logger.info(f"User {current_user.username} retrieving own profile by ID")
        return current_user
    
    # For viewing other users, check permissions using the decorator's logic
    from app.core.permissions import has_permission
    user_roles = current_user.get_roles()
    
    if not has_permission(user_roles, Permission.USER_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view other users"
        )
    
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User {current_user.username} retrieving user {user.username}")
    return user

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
    current_user: User = Depends(require_permissions(Permission.USER_CREATE)),
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
    
    # For updating other users, check permissions  
    from app.core.permissions import has_permission
    user_roles = current_user.get_roles()
    
    if not has_permission(user_roles, Permission.USER_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only managers can update other users."
        )
    
    target_user = user_crud.get(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = user_crud.update(db, user_data, user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    logger.info(f"Manager {current_user.username} updated user {updated_user.username}")
    return updated_user

@router.put("/{user_id}/roles", response_model=UserRead)
async def update_user_roles(
    user_id: uuid.UUID,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_permissions(Permission.USER_ROLE_UPDATE)),
    db: Session = Depends(get_db)
):
    """Update user roles (Manager only)"""
    target_user = user_crud.get(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate roles
    try:
        valid_roles = [UserRole(role) for role in role_data.roles if role in [r.value for r in UserRole]]
        if not valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid roles provided"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role provided"
        )
    
    # Update user roles
    import json
    target_user.roles = json.dumps([role.value for role in valid_roles])
    
    user_update = UserUpdate(roles=target_user.roles)
    updated_user = user_crud.update(db, user_update, user_id)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user roles"
        )
    
    logger.info(f"Manager {current_user.username} updated roles for user {updated_user.username}")
    return updated_user

@router.delete("/{user_id}", response_model=UserRead)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permissions(Permission.USER_DELETE)),
    db: Session = Depends(get_db)
):
    """Delete user (Manager only)"""
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted_user = user_crud.delete(db, user_id)
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Manager {current_user.username} deleted user {deleted_user.username}")
    return deleted_user
