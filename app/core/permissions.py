# filepath: app/core/permissions.py
from enum import Enum
from typing import Dict, Set, Optional
from ..models.project_member import ProjectRole

class Permission(str, Enum):
    """User permissions for application features - project-specific permissions only"""
    # Project Management
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
    
    # File Management
    FILE_READ = "file:read"
    FILE_CREATE = "file:create"
    FILE_UPDATE = "file:update"
    FILE_DELETE = "file:delete"
    DIRECTORY_CREATE = "directory:create"
    
    # AI Functions (for regular users)
    AI_RTM_GENERATE = "ai:rtm_generate"
    AI_CHAT = "ai:chat"
    AI_ANALYZE = "ai:analyze"
    
    # Chat Functions
    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"
    CHAT_DELETE = "chat:delete"

# Project role-permission mapping
PROJECT_ROLE_PERMISSIONS: Dict[ProjectRole, Set[Permission]] = {
    ProjectRole.MANAGER: {
        # Full project management capabilities
        Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.DOCUMENT_CREATE, Permission.DOCUMENT_READ, Permission.DOCUMENT_UPDATE, 
        Permission.DOCUMENT_DELETE,
        Permission.ARTIFACT_CREATE, Permission.ARTIFACT_READ, Permission.ARTIFACT_UPDATE, 
        Permission.ARTIFACT_DELETE,
        # Full file management capabilities
        Permission.FILE_READ, Permission.FILE_CREATE, Permission.FILE_UPDATE, 
        Permission.FILE_DELETE, Permission.DIRECTORY_CREATE,
        Permission.AI_RTM_GENERATE, Permission.AI_CHAT, Permission.AI_ANALYZE,
        Permission.CHAT_CREATE, Permission.CHAT_READ, Permission.CHAT_DELETE
    },
    ProjectRole.TESTER: {
        # Testing operations with some project management
        Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.DOCUMENT_CREATE, Permission.DOCUMENT_READ, Permission.DOCUMENT_UPDATE,
        Permission.ARTIFACT_CREATE, Permission.ARTIFACT_READ, Permission.ARTIFACT_UPDATE,
        # File operations except delete
        Permission.FILE_READ, Permission.FILE_CREATE, Permission.FILE_UPDATE, 
        Permission.DIRECTORY_CREATE,
        Permission.AI_RTM_GENERATE, Permission.AI_CHAT,
        Permission.CHAT_CREATE, Permission.CHAT_READ, Permission.CHAT_DELETE
    },
    ProjectRole.VIEWER: {
        # Read-only access
        Permission.PROJECT_READ,
        Permission.DOCUMENT_READ,
        Permission.ARTIFACT_READ,
        # Read-only file access
        Permission.FILE_READ,
        Permission.CHAT_READ
    }
}

def has_project_permission(project_role: Optional[ProjectRole], permission: Permission) -> bool:
    """
    Check if user with given project role has the specified permission
    
    Args:
        project_role: Project role of the user (None if not a project member)
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    if not project_role or project_role not in PROJECT_ROLE_PERMISSIONS:
        return False
    return permission in PROJECT_ROLE_PERMISSIONS[project_role]

def get_project_permissions(project_role: Optional[ProjectRole]) -> Set[Permission]:
    """
    Get all permissions for a user based on their project role
    
    Args:
        project_role: Project role of the user
        
    Returns:
        Set of all permissions for the user in this project
    """
    if not project_role or project_role not in PROJECT_ROLE_PERMISSIONS:
        return set()
    return PROJECT_ROLE_PERMISSIONS[project_role].copy()

def can_access_ai_rtm(project_role: Optional[ProjectRole]) -> bool:
    """Check if user can access AI RTM generation in this project"""
    return has_project_permission(project_role, Permission.AI_RTM_GENERATE)
