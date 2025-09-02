# filepath: app/core/auth.py
from functools import wraps
from typing import Optional, List
from fastapi import HTTPException, status, Depends
from sqlmodel import Session
from .database import get_db
from .permissions import Permission, has_project_permission, PROJECT_ROLE_PERMISSIONS
from ..models.user import User
from ..models.project_member import ProjectRole
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

def require_project_permission(permission: Permission):
    """Decorator to require specific permission within a project context"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user and project_id from kwargs
            current_user: Optional[User] = kwargs.get('current_user')
            project_id = kwargs.get('project_id')
            
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
            
            # Get user's role in this specific project
            project_role = current_user.get_project_role(project_id)
            if not has_project_permission(project_role, permission):
                logger.warning(
                    f"User {current_user.username} with project role {project_role} "
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

def require_project_roles(roles: List[ProjectRole]):
    """Decorator to require specific project roles for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[User] = kwargs.get('current_user')
            project_id = kwargs.get('project_id')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            project_role = current_user.get_project_role(project_id)
            if not project_role or project_role not in roles:
                logger.warning(
                    f"User {current_user.username} denied access to {func.__name__} "
                    f"(requires one of: {[r.value for r in roles]}, has: {project_role})"
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
