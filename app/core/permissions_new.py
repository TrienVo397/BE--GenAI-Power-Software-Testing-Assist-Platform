# filepath: app/core/permissions.py
from enum import Enum
from typing import Dict, List, Set
from ..models.user import UserRole

class Permission(str, Enum):
    """Regular user permissions for application features (separated from admin permissions)"""
    # Project Management
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    
    # Document Management
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    
    # Artifact Management
    ARTIFACT_CREATE = "artifact:create"
    ARTIFACT_READ = "artifact:read"
    ARTIFACT_UPDATE = "artifact:update"
    ARTIFACT_DELETE = "artifact:delete"
    
    # AI Functions (for regular users)
    AI_RTM_GENERATE = "ai:rtm_generate"
    AI_CHAT = "ai:chat"
    AI_ANALYZE = "ai:analyze"
    
    # Chat Functions
    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"
    CHAT_DELETE = "chat:delete"

# Regular user role-permission mapping (non-admin users)
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.MANAGER: {
        # Full project management capabilities
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, 
        Permission.PROJECT_DELETE,
        Permission.DOCUMENT_CREATE, Permission.DOCUMENT_READ, Permission.DOCUMENT_UPDATE, 
        Permission.DOCUMENT_DELETE,
        Permission.ARTIFACT_CREATE, Permission.ARTIFACT_READ, Permission.ARTIFACT_UPDATE, 
        Permission.ARTIFACT_DELETE,
        Permission.AI_RTM_GENERATE, Permission.AI_CHAT, Permission.AI_ANALYZE,
        Permission.CHAT_CREATE, Permission.CHAT_READ, Permission.CHAT_DELETE
    },
    UserRole.TESTER: {
        # Testing operations with some project management
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.DOCUMENT_CREATE, Permission.DOCUMENT_READ, Permission.DOCUMENT_UPDATE,
        Permission.ARTIFACT_CREATE, Permission.ARTIFACT_READ, Permission.ARTIFACT_UPDATE,
        Permission.AI_RTM_GENERATE, Permission.AI_CHAT,
        Permission.CHAT_CREATE, Permission.CHAT_READ, Permission.CHAT_DELETE
    },
    UserRole.VIEWER: {
        # Read-only access
        Permission.PROJECT_READ,
        Permission.DOCUMENT_READ,
        Permission.ARTIFACT_READ,
        Permission.CHAT_READ
    }
}

def has_permission(user_roles: List[UserRole], permission: Permission) -> bool:
    """
    Check if user with given roles has the specified permission
    
    Args:
        user_roles: List of user roles
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            if permission in ROLE_PERMISSIONS[role]:
                return True
    return False

def get_user_permissions(user_roles: List[UserRole]) -> Set[Permission]:
    """
    Get all permissions for a user based on their roles
    
    Args:
        user_roles: List of user roles
        
    Returns:
        Set of all permissions for the user
    """
    permissions = set()
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    return permissions

def can_access_ai_rtm(user_roles: List[UserRole]) -> bool:
    """Check if user can access AI RTM generation"""
    return has_permission(user_roles, Permission.AI_RTM_GENERATE)
