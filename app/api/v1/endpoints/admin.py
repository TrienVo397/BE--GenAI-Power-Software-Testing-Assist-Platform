# filepath: app/api/v1/endpoints/admin.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
import uuid

from app.core.database import get_db
from app.core.admin_auth import get_current_admin
from app.models.admin import Admin
from app.models.user import User
from app.schemas.admin import (
    AdminCreate, AdminUpdate, AdminRead, AdminProfile,
    AdminSummary, AdminToken, AdminRegister
)
from app.schemas.user import UserRead, UserUpdate, AdminUserCreate, AdminUserUpdate, Token
from app.crud.admin_crud import admin_crud
from app.crud.admin_credential_crud import admin_credential_crud
from app.crud.user_crud import user_crud
from app.core.security import verify_password, create_access_token
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Admin Authentication Endpoints
@router.post("/register", response_model=AdminRead)
async def register_first_admin(
    admin_data: AdminRegister,
    db: Session = Depends(get_db)
):
    """Register the first admin (only works if no admins exist)"""
    # Check if any admins already exist
    existing_admins = admin_crud.get_multi(db, limit=1)
    if existing_admins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin registration is closed. First admin already exists."
        )
    
    # Check if admin username or email already exists
    existing_admin = admin_crud.get_by_username(db, admin_data.admin_username)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin username already registered"
        )
    
    existing_admin = admin_crud.get_by_email(db, admin_data.admin_email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email already registered"
        )
    
    # Create first admin
    admin_create_data = {
        "admin_username": admin_data.admin_username,
        "admin_email": admin_data.admin_email,
        "full_name": admin_data.full_name,
        "department": admin_data.department
    }
    
    new_admin = admin_crud.create(db, admin_create_data)
    
    # Create admin credential
    admin_credential_crud.create(db, new_admin.id, admin_data.password)
    
    logger.info(f"First admin created: {new_admin.admin_username}")
    return new_admin

@router.post("/login", response_model=AdminToken)
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint (OAuth2 compatible for Swagger UI) - supports username or email
    
    The username field accepts either:
    - Admin username (e.g., "admin_user")
    - Admin email address (e.g., "admin@example.com")
    """
    # Try to find admin by username or email
    admin = admin_crud.get_by_username_or_email(db, form_data.username)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    is_valid = admin_credential_crud.verify_password(db, admin.id, form_data.password)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    from datetime import datetime, timezone, timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)  # Admin tokens expire in 8 hours
    
    access_token = create_access_token(
        data={"sub": str(admin.id), "type": "admin"},
        expires_delta=timedelta(hours=8)
    )
    
    # Update last login
    admin_crud.update(db, admin.id, {"last_login": datetime.now(timezone.utc)})
    
    return AdminToken(
        access_token=access_token,
        token_type="bearer",
        admin_id=admin.id,
        admin_username=admin.admin_username,
        permissions=["all"],  # All admins have full access
        expires_at=expires_at
    )

@router.get("/whoami", response_model=AdminProfile)
async def admin_whoami(current_admin: Admin = Depends(get_current_admin)):
    """Get current admin profile (whoami)"""
    return AdminProfile(
        id=current_admin.id,
        admin_username=current_admin.admin_username,
        admin_email=current_admin.admin_email,
        full_name=current_admin.full_name,
        department=current_admin.department,
        notes=current_admin.notes,
        admin_roles=["admin"],  # Simple admin role
        permissions=["all"],    # All admins have full access
        is_active=current_admin.is_active,
        is_super_admin=True,    # All admins are considered super admins
        requires_2fa=False,     # Simplified - no 2FA requirement
        created_at=current_admin.created_at,
        updated_at=current_admin.updated_at,
        last_login=current_admin.last_login,
        created_by=current_admin.created_by,
        linked_user_id=current_admin.linked_user_id
    )

# Admin Management Endpoints - All authenticated admins have access
@router.get("/profile", response_model=AdminProfile)
async def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin)
):
    """Get current admin's profile"""
    logger.info(f"Admin {current_admin.admin_username} retrieving own profile")
    
    return AdminProfile(
        id=current_admin.id,
        admin_username=current_admin.admin_username,
        admin_email=current_admin.admin_email,
        full_name=current_admin.full_name,
        department=current_admin.department,
        notes=current_admin.notes,
        admin_roles=["admin"],  # Simple admin role
        permissions=["all"],    # All admins have full access
        is_active=current_admin.is_active,
        is_super_admin=True,    # All admins are considered super admins
        requires_2fa=False,     # Simplified - no 2FA requirement
        created_at=current_admin.created_at,
        updated_at=current_admin.updated_at,
        last_login=current_admin.last_login,
        created_by=current_admin.created_by,
        linked_user_id=current_admin.linked_user_id
    )

@router.get("/all", response_model=List[AdminSummary])
async def get_all_admins(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get list of all admins - all authenticated admins have access"""
    logger.info(f"Admin {current_admin.admin_username} retrieving all admins")
    admins = admin_crud.get_multi(db, skip=skip, limit=limit)
    return admins

@router.get("/{admin_id}", response_model=AdminRead)
async def get_admin_by_id(
    admin_id: uuid.UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin by ID - all authenticated admins have access"""
    admin = admin_crud.get(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    logger.info(f"Admin {current_admin.admin_username} retrieving admin {admin.admin_username}")
    return admin

@router.post("/create", response_model=AdminRead)
async def create_admin(
    admin_data: AdminCreate,
    password: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new admin - all authenticated admins have access"""
    # Check if admin already exists
    existing_admin = admin_crud.get_by_username(db, admin_data.admin_username)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin username already registered"
        )
    
    existing_admin = admin_crud.get_by_email(db, admin_data.admin_email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email already registered"
        )
    
    # Create admin
    admin_create_data = admin_data.dict()
    admin_create_data["created_by"] = current_admin.id
    
    new_admin = admin_crud.create(db, admin_create_data)
    
    # Create admin credential
    admin_credential_crud.create(db, new_admin.id, password)
    
    logger.info(f"Admin {current_admin.admin_username} created new admin {new_admin.admin_username}")
    return new_admin

@router.put("/{admin_id}", response_model=AdminRead)
async def update_admin(
    admin_id: uuid.UUID,
    admin_data: AdminUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update admin - all authenticated admins have access"""
    target_admin = admin_crud.get(db, admin_id)
    if not target_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    updated_admin = admin_crud.update(db, admin_id, admin_data.dict(exclude_unset=True))
    
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin"
        )
    
    logger.info(f"Admin {current_admin.admin_username} updated admin {updated_admin.admin_username}")
    return updated_admin

# User Management via Admin - All authenticated admins have access
@router.get("/users/all", response_model=List[UserRead])
async def admin_get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users - all authenticated admins have access"""
    logger.info(f"Admin {current_admin.admin_username} retrieving all users")
    users = user_crud.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/users/create", response_model=UserRead)
async def admin_create_user(
    user_data: AdminUserCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create user via admin - all authenticated admins have access"""
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
    
    # Create user (implementation depends on your user creation logic)
    from app.schemas.user import UserCreate
    user_create = UserCreate(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    new_user = user_crud.create(db, user_create)
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    logger.info(f"Admin {current_admin.admin_username} created user {new_user.username}")
    return new_user

@router.put("/users/{user_id}", response_model=UserRead)
async def admin_update_user(
    user_id: uuid.UUID,
    user_data: AdminUserUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user via admin - all authenticated admins have access"""
    target_user = user_crud.get(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert to UserUpdate
    update_dict = user_data.dict(exclude_unset=True, exclude={'roles'})
    user_update = UserUpdate(**update_dict)
    
    updated_user = user_crud.update(db, user_update, user_id)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    logger.info(f"Admin {current_admin.admin_username} updated user {updated_user.username}")
    return updated_user

@router.delete("/users/{user_id}", response_model=UserRead)
async def admin_delete_user(
    user_id: uuid.UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete user via admin - all authenticated admins have access"""
    deleted_user = user_crud.delete(db, user_id)
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Admin {current_admin.admin_username} deleted user {deleted_user.username}")
    return deleted_user