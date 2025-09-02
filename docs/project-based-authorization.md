# Project-Based Authorization System

## Overview

This document describes the project-based authorization system implemented in the GenAI-powered software testing assistance platform. The system has moved from global user roles to a pure project-based role model where users are assigned specific roles within individual projects.

## Architecture

### Core Principles

1. **No Global User Roles**: Users exist without any global role assignments
2. **Project-Specific Permissions**: All permissions are granted through project membership
3. **Fixed Role Types**: Three predefined roles with clear permission boundaries
4. **Membership-Based Access**: Users can only access projects they are members of

### Dual Authentication System

The platform maintains a dual authentication system:

- **Admin System**: Separate admin users with full platform access
- **User System**: Regular users with project-based permissions only

## Project Roles

### Role Hierarchy

| Role | Level | Description |
|------|-------|-------------|
| **MANAGER** | High | Full project control including member management |
| **TESTER** | Medium | Can create and modify test content |
| **VIEWER** | Low | Read-only access to project content |

### Role Permissions Matrix

| Permission | MANAGER | TESTER | VIEWER |
|------------|---------|--------|--------|
| View project content | ✅ | ✅ | ✅ |
| Create/edit artifacts | ✅ | ✅ | ❌ |
| Delete artifacts | ✅ | ❌ | ❌ |
| Upload/manage files | ✅ | ✅ | ❌ |
| Manage document versions | ✅ | ✅ | ❌ |
| Add/remove project members | ✅ | ❌ | ❌ |
| Change member roles | ✅ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ |
| AI chat and generation | ✅ | ✅ | ✅ |

## Database Models

### Project Model
```python
class Project(SQLModel, table=True):
    id: uuid.UUID
    name: str
    created_by: uuid.UUID  # User who created the project
    members: List["ProjectMember"]  # Project memberships
    # ... other project fields
```

### ProjectMember Model
```python
class ProjectMember(SQLModel, table=True):
    project_id: uuid.UUID  # FK to Project
    user_id: uuid.UUID     # FK to User
    role: ProjectRole      # MANAGER, TESTER, or VIEWER
    is_active: bool        # Can disable membership temporarily
    joined_at: datetime
    added_by: uuid.UUID    # Who added this member
```

### User Model (Updated)
```python
class User(SQLModel, table=True):
    id: uuid.UUID
    username: str
    email: str
    # No global roles field
    project_memberships: List["ProjectMember"]
    
    # Project-specific permission methods
    def is_project_member(self, project_id: uuid.UUID) -> bool
    def get_project_role(self, project_id: uuid.UUID) -> Optional[ProjectRole]
    def can_modify_project_content(self, project_id: uuid.UUID) -> bool
    def can_manage_project_members(self, project_id: uuid.UUID) -> bool
```

## API Endpoints

### Project Membership Management

```http
# Get project members
GET /api/v1/projects/{project_id}/members

# Add member to project (MANAGER only)
POST /api/v1/projects/{project_id}/members
{
  "user_id": "uuid",
  "role": "TESTER"
}

# Update member role (MANAGER only)
PUT /api/v1/projects/{project_id}/members/{user_id}
{
  "role": "VIEWER"
}

# Remove member from project (MANAGER only)
DELETE /api/v1/projects/{project_id}/members/{user_id}

# Get available roles
GET /api/v1/project-roles
```

### Authorization Patterns

All API endpoints now follow project-based authorization:

```python
@router.get("/api/v1/projects/{project_id}/artifacts")
async def get_project_artifacts(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user is a member of the project
    if not current_user.is_project_member(project_id):
        raise HTTPException(403, "Access denied: Not a project member")
    
    # Proceed with operation...
```

## Implementation Guide

### Creating a New Project

When a user creates a project:
1. Project is created with `created_by` set to the user
2. User is automatically assigned as MANAGER of the project
3. User can then invite other members with appropriate roles

### Adding Project Members

Only users with MANAGER role can add members:
```python
# Check permission
if not current_user.can_manage_project_members(project_id):
    raise HTTPException(403, "Only project managers can add members")

# Add member
project_member_crud.add_member(
    db=db,
    project_id=project_id,
    member_data=ProjectMemberCreate(user_id=new_user_id, role=ProjectRole.TESTER),
    added_by=current_user.id
)
```

### Permission Checking Patterns

```python
# Basic membership check
if not current_user.is_project_member(project_id):
    raise HTTPException(403, "Access denied")

# Content modification check
if not current_user.can_modify_project_content(project_id):
    raise HTTPException(403, "Insufficient permissions")

# Member management check
if not current_user.can_manage_project_members(project_id):
    raise HTTPException(403, "Only managers can modify memberships")

# Role-specific check
user_role = current_user.get_project_role(project_id)
if user_role != ProjectRole.MANAGER:
    raise HTTPException(403, "Manager role required")
```

## Migration from Global Roles

### What Changed

1. **Removed Global UserRole Enum**: No more global MANAGER/TESTER/VIEWER roles
2. **Removed Global Permissions System**: No more `has_permission()` or `get_roles()` methods
3. **Removed RBAC System**: Deprecated all dynamic role/permission models
4. **Added Project Membership**: Users are assigned roles per project

### Updated User Creation

```python
# OLD: Users created with global roles
user = User(username="john", email="john@example.com", roles='["manager"]')

# NEW: Users created without roles
user = User(username="john", email="john@example.com")
# Roles assigned through project membership
```

## Security Considerations

### Access Control
- Users can only see projects they are members of
- All project operations require membership validation
- Role escalation requires MANAGER permissions

### Audit Trail
- All membership changes are logged with timestamps
- `added_by` and `updated_by` fields track who made changes
- Membership history is preserved through audit fields

### Data Isolation
- Projects are completely isolated from each other
- Users cannot access data from projects they're not members of
- Cross-project operations are not permitted

## Testing the System

### Sample Data
The system includes seed data with:
- 3 users: `user1`, `user2`, `user3`
- 1 sample project created by `user1`
- `user1` assigned as MANAGER of the sample project
- `user2` and `user3` available for assignment

### Test Scenarios

1. **Project Creation**:
   - Login as any user
   - Create a new project
   - Verify automatic MANAGER assignment

2. **Member Management**:
   - Login as `user1` (MANAGER)
   - Add `user2` as TESTER
   - Add `user3` as VIEWER
   - Test role-based access

3. **Permission Validation**:
   - Login as `user2` (TESTER)
   - Try to add members (should fail)
   - Create artifacts (should succeed)

4. **Access Control**:
   - Login as `user3` (VIEWER)
   - View project content (should succeed)
   - Try to modify content (should fail)

## API Documentation

For detailed API documentation, see:
- [Project API](./project-api.md)
- [Project Member API](./project-member-api.md)
- [Authentication Guide](./authentication.md)

## Troubleshooting

### Common Issues

1. **403 Access Denied**: User is not a member of the project
2. **404 Project Not Found**: User cannot see projects they're not members of
3. **Insufficient Permissions**: User role doesn't allow the requested operation

### Debug Tips

```python
# Check user's project memberships
user_memberships = user.project_memberships
print(f"User is member of {len(user_memberships)} projects")

# Check specific project role
role = user.get_project_role(project_id)
print(f"User role in project: {role}")

# Verify permissions
can_modify = user.can_modify_project_content(project_id)
can_manage = user.can_manage_project_members(project_id)
print(f"Can modify: {can_modify}, Can manage: {can_manage}")
```
