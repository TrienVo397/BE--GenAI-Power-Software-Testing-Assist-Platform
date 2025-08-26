# filepath: app/crud/rbac_crud.py
"""
DEPRECATED: Dynamic RBAC CRUD operations
This module has been removed because the system now uses fixed project-based roles:
- MANAGER: Full project control
- TESTER: Can create/update artifacts and test cases  
- VIEWER: Read-only access

Use app/crud/project_member_crud.py for role management instead.
"""

# No CRUD operations - use project membership system instead
