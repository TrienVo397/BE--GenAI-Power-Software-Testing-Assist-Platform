# filepath: app/core/permissions_new.py
"""
DEPRECATED: Global user role permissions system
This module has been removed because the system now uses project-based roles only.

The new system uses:
- Fixed project roles: MANAGER, TESTER, VIEWER
- Project-specific permissions through ProjectMember model
- No global user roles

Use app/models/project_member.py and User model methods instead:
- user.is_project_member(project_id)
- user.can_modify_project_content(project_id)  
- user.can_manage_project_members(project_id)
"""

# No permissions system - use project membership methods instead
