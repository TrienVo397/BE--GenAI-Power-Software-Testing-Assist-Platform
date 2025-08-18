# filepath: app/core/authz.py
"""
Authorization system for FastAPI endpoints that preserves OpenAPI schema generation
"""
from typing import List, Optional, Union
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.permissions import Permission, has_permission
from app.core.security import get_current_user, decode_access_token
from app.models.user import User

logger = logging.getLogger(__name__)

# OAuth2 schemes for both admin and user authentication
user_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login",
    scheme_name="UserOAuth2PasswordBearer"
)

admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/admin/login", 
    scheme_name="AdminOAuth2PasswordBearer"
)

async def get_token_from_either_scheme(
    user_token: Optional[str] = Depends(user_oauth2_scheme, use_cache=False),
    admin_token: Optional[str] = Depends(admin_oauth2_scheme, use_cache=False)
) -> str:
    """
    Get token from either user or admin OAuth2 scheme.
    This allows Swagger UI to show both authentication options.
    """
    # Return whichever token is provided
    if admin_token:
        return admin_token
    elif user_token:
        return user_token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

async def get_current_user_or_admin(
    token: str = Depends(get_token_from_either_scheme),
    db = Depends(lambda: None)  # We'll get db in the function
) -> tuple[Optional[User], bool]:
    """
    Get current user or determine if it's an admin token.
    Returns (user, is_admin) tuple.
    """
    from app.api.deps import get_db
    from sqlmodel import Session
    
    # Get database session
    if db is None:
        # This is a fallback, in practice db should be passed properly
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session required"
        )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Decode the JWT token
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        user_id_str = payload.get("sub")
        token_type = payload.get("type", "user")  # Default to user if not specified
        
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        import uuid
        
        if token_type == "admin":
            # This is an admin token - verify admin exists and return admin flag
            from app.crud.admin_crud import admin_crud
            admin_uuid = uuid.UUID(user_id_str)
            admin = admin_crud.get(db, admin_uuid)
            
            if not admin or not admin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid admin authentication"
                )
            
            logger.info(f"Admin {admin.admin_username} accessing user API with full privileges")
            return None, True  # No user object, but is admin
            
        else:
            # This is a user token - get the user
            from app.crud import user_crud
            user_uuid = uuid.UUID(user_id_str)
            user = user_crud.get(db, user_uuid)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
                
            return user, False  # User object, not admin
            
    except ValueError as e:
        logger.error(f"Error parsing UUID: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Error in authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

class AuthorizationDependency:
    """
    FastAPI dependency class for authorization that preserves OpenAPI schema generation.
    
    Supports both user and admin authentication:
    - Users: Role-based permissions (Manager, Tester, Viewer)  
    - Admins: Full access to all user APIs when authenticated
    """
    
    def __init__(self, *required_permissions: Permission):
        self.required_permissions = required_permissions
    
    async def __call__(
        self, 
        token: str = Depends(get_token_from_either_scheme),
    ) -> User:
        """
        Check if the current user has the required permissions or is an admin.
        Admins have full access to all user APIs.
        Returns a user object if authorized, raises HTTPException if not.
        """
        from app.api.deps import get_db
        from sqlmodel import Session
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            user, is_admin = await get_current_user_or_admin(token, db)
            
            # If admin, allow full access
            if is_admin:
                logger.info(f"Admin token detected - granting full access to user API")
                # Return a dummy user object for compatibility
                import uuid
                from app.models.user import User
                admin_user = User(
                    id=uuid.uuid4(),  # Generate a dummy UUID for admin
                    username="[ADMIN]", 
                    email="admin@system.internal",
                    full_name="System Administrator",
                    roles='["admin"]',
                    is_active=True,
                    is_verified=True
                )
                return admin_user
            
            # Regular user - check permissions
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization requires authenticated user"
                )
            
            # Get user roles and check permissions
            user_roles = user.get_roles()
            
            missing_permissions = []
            for permission in self.required_permissions:
                if not has_permission(user_roles, permission):
                    missing_permissions.append(permission.value)
            
            if missing_permissions:
                logger.warning(
                    f"User {user.username} ({user_roles}) attempted to access "
                    f"endpoint without required permissions: {missing_permissions}"
                )
                
                if len(missing_permissions) == 1:
                    detail = f"Insufficient permissions. Required permission: {missing_permissions[0]}"
                else:
                    detail = f"Insufficient permissions. Required permissions: {', '.join(missing_permissions)}"
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=detail
                )
            
            # Log successful authorization
            logger.info(
                f"User {user.username} ({user_roles}) authorized with permissions: "
                f"{[p.value for p in self.required_permissions]}"
            )
            
            return user
            
        finally:
            # Close the database session
            try:
                db.close()
            except:
                pass

# Convenience functions to create authorization dependencies
def require_permissions(*permissions: Permission) -> AuthorizationDependency:
    """
    Create an authorization dependency that requires specific permissions.
    
    Usage:
        def my_endpoint(
            authorized_user: User = Depends(require_permissions(Permission.CHAT_CREATE))
        ):
            pass
    """
    return AuthorizationDependency(*permissions)

def require_manager() -> AuthorizationDependency:
    """Create an authorization dependency for manager-only operations"""
    return AuthorizationDependency(Permission.USER_CREATE)  # Only managers have this

def require_manager_or_tester() -> AuthorizationDependency:
    """Create an authorization dependency for manager/tester operations"""
    return AuthorizationDependency(Permission.PROJECT_CREATE)  # Both have this

def require_authenticated() -> AuthorizationDependency:
    """Create an authorization dependency for any authenticated user"""  
    return AuthorizationDependency(Permission.USER_READ)  # All roles have this


# Migration complete! All endpoints now use dependency-based authorization.
# The @authz decorator has been fully replaced with Depends(require_permissions())
