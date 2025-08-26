# filepath: app/api/v1/endpoints/rbac.py
"""
DEPRECATED: Dynamic RBAC system removed
This system used dynamic user roles, which have been replaced with fixed project-based roles:
- MANAGER: Full project control
- TESTER: Can create/update artifacts and test cases  
- VIEWER: Read-only access

All role management is now handled through project membership.
See: app/api/v1/endpoints/project_members.py
"""
from fastapi import APIRouter

router = APIRouter()

# No endpoints - RBAC system has been removed
# Use project membership endpoints for role management
