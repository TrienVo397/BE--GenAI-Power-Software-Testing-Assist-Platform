# filepath: app/core/auth.py
from functools import wraps
from typing import Optional, List
from fastapi import HTTPException, status, Depends
from sqlmodel import Session
from .database import get_db
from .permissions import Permission, has_permission
from ..models.user import User, UserRole
from ..crud.user_crud import user_crud
import logging
import uuid

logger = logging.getLogger(__name__)

# This should be implemented based on your authentication system
# For now, this is a placeholder - you'll need to integrate with your JWT/session system
async def get_current_user(
    # Add your authentication parameters here (JWT token, session, etc.)
    user_id: Optional[str] = None,  # This should come from your auth system
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from session/token
    TODO: Integrate with your actual authentication system
    """
    if not user_id:
        # In a real implementation, this would extract user_id from JWT token or session
        # For now, we'll raise an exception to indicate authentication is required
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        user_uuid = uuid.UUID(user_id)
        user = user_crud.get(db, user_uuid)
        if user and user.is_active:
            return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication"
    )

def require_permission(permission: Permission):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user from kwargs or dependencies
            current_user: Optional[User] = kwargs.get('current_user')
            
            if not current_user:
                logger.warning(f"Unauthorized access attempt to {func.__name__}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not current_user.is_active:
                logger.warning(f"Inactive user {current_user.username} attempted to access {func.__name__}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive"
                )
            
            user_roles = current_user.get_roles()
            if not has_permission(user_roles, permission):
                logger.warning(
                    f"User {current_user.username} with roles {[r.value for r in user_roles]} "
                    f"denied access to {func.__name__} (requires {permission.value})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )
            
            logger.info(f"User {current_user.username} authorized for {func.__name__}")
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_roles(roles: List[UserRole]):
    """Decorator to require specific roles for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[User] = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not current_user.has_any_role(roles):
                logger.warning(
                    f"User {current_user.username} denied access to {func.__name__} "
                    f"(requires one of: {[r.value for r in roles]})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {[r.value for r in roles]}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Note: admin_required decorator has been moved to admin_auth.py
# Admin functionality is now handled by the separate Admin model and admin authentication system
