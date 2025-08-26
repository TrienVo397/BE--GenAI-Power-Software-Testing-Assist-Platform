# System Migration Summary: Global to Project-Based Authorization

## Overview

This document summarizes the complete migration from a global user role system to a project-based authorization system in the GenAI-powered software testing assistance platform.

## Migration Summary

### 🗑️ **REMOVED - Global Role System**

#### Deprecated Files (Completely Removed):
- `app/models/rbac.py` - Dynamic RBAC models
- `app/schemas/rbac.py` - Dynamic RBAC schemas  
- `app/crud/rbac_crud.py` - Dynamic RBAC operations
- `app/api/v1/endpoints/rbac.py` - RBAC endpoints
- `app/core/permissions_new.py` - Global permission system

#### Removed Features:
- ❌ Global `UserRole` enum (MANAGER, TESTER, VIEWER)
- ❌ Global permissions system (`has_permission()`, `get_roles()`)
- ❌ User `roles` field in database model
- ❌ Global RBAC dynamic role assignments
- ❌ Cross-project access rights
- ❌ Global permission validation patterns

### ✅ **ADDED - Project-Based System**

#### New Models:
- `ProjectMember` model for project-specific role assignments
- Fixed `ProjectRole` enum (MANAGER, TESTER, VIEWER)
- Project membership relationships

#### New Features:
- ✅ Project-specific role assignments
- ✅ Complete project isolation
- ✅ Project membership management APIs
- ✅ User model methods for project permissions
- ✅ Project-scoped authorization patterns
- ✅ Membership audit trails

## Technical Changes

### Database Schema Updates

#### User Model (Before):
```python
class User(SQLModel, table=True):
    id: uuid.UUID
    username: str
    email: str
    roles: str  # JSON array: ["manager", "tester", "viewer"]
    # ... other fields
```

#### User Model (After):
```python
class User(SQLModel, table=True):
    id: uuid.UUID
    username: str
    email: str
    # REMOVED: roles field
    project_memberships: List["ProjectMember"] = Relationship(...)
    # ... other fields
    
    # NEW: Project-specific permission methods
    def is_project_member(self, project_id: uuid.UUID) -> bool
    def get_project_role(self, project_id: uuid.UUID) -> Optional[ProjectRole]
    def can_modify_project_content(self, project_id: uuid.UUID) -> bool
    def can_manage_project_members(self, project_id: uuid.UUID) -> bool
```

#### New ProjectMember Model:
```python
class ProjectMember(SQLModel, table=True):
    project_id: uuid.UUID  # FK to Project
    user_id: uuid.UUID     # FK to User  
    role: ProjectRole      # MANAGER, TESTER, VIEWER
    is_active: bool = True
    joined_at: datetime
    added_by: Optional[uuid.UUID]
    updated_by: Optional[uuid.UUID]
```

### Authorization Pattern Changes

#### Before (Global Permissions):
```python
# OLD: Global role-based authorization
@router.post("/projects/")
async def create_project(
    current_user: User = Depends(require_permissions([Permission.PROJECT_CREATE]))
):
    # Global permission check
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, Permission.PROJECT_CREATE):
        raise HTTPException(403, "Insufficient permissions")
```

#### After (Project-Based):
```python
# NEW: Project membership authorization
@router.get("/projects/{project_id}/artifacts")
async def get_project_artifacts(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    # Project membership check
    if not current_user.is_project_member(project_id):
        raise HTTPException(403, "Access denied: Not a project member")
    
    # Role-specific checks
    if operation_requires_modification:
        if not current_user.can_modify_project_content(project_id):
            raise HTTPException(403, "Insufficient permissions")
```

## API Changes

### New Project Member Management APIs

```http
# Get available project roles
GET /api/v1/project-roles

# Project membership management
GET    /api/v1/projects/{project_id}/members
POST   /api/v1/projects/{project_id}/members
PUT    /api/v1/projects/{project_id}/members/{user_id}
DELETE /api/v1/projects/{project_id}/members/{user_id}
POST   /api/v1/projects/{project_id}/members/bulk

# User project memberships
GET /api/v1/users/{user_id}/projects
```

### Updated Existing APIs

All user APIs now require project membership validation:

#### Projects API:
- `GET /projects/` - Only shows projects where user is a member
- `GET /projects/{id}` - Requires project membership
- `PUT /projects/{id}` - Requires MANAGER role
- `DELETE /projects/{id}` - Requires MANAGER role

#### Artifacts API:
- All endpoints now validate project membership
- Create/Update operations require MANAGER or TESTER role
- Delete operations require MANAGER role only

#### Files API:
- File access requires project membership
- Upload/modify operations require MANAGER or TESTER role
- Delete operations require MANAGER role only

## Seeded Data Changes

### Before:
```
Manager User:
- Email: manager@example.com
- Password: manager123  
- Global Role: MANAGER

Tester User:
- Email: tester@example.com
- Password: tester123
- Global Role: TESTER

Viewer User:
- Email: viewer@example.com
- Password: viewer123
- Global Role: VIEWER
```

### After:
```
User 1:
- Email: user1@example.com
- Password: user123
- Global Role: None
- Project Role: MANAGER of "Sample Testing Project"

User 2:
- Email: user2@example.com
- Password: user123
- Global Role: None
- Project Role: Not assigned to any project

User 3:
- Email: user3@example.com
- Password: user123
- Global Role: None
- Project Role: Not assigned to any project
```

## Permission Matrix Comparison

### Global System (Old):
| Operation | Manager | Tester | Viewer |
|-----------|---------|--------|--------|
| Access ANY project | ✅ | ✅ | ✅ |
| Create projects | ✅ | ✅ | ❌ |
| Delete ANY artifact | ✅ | ❌ | ❌ |
| View ALL user data | ✅ | ✅ | ✅ |

### Project-Based System (New):
| Operation | MANAGER | TESTER | VIEWER | Non-Member |
|-----------|---------|--------|--------|------------|
| Access project | ✅ | ✅ | ✅ | ❌ |
| Modify project content | ✅ | ✅ | ❌ | ❌ |
| Delete project artifacts | ✅ | ❌ | ❌ | ❌ |
| Manage members | ✅ | ❌ | ❌ | ❌ |

## Security Improvements

### Enhanced Isolation:
1. **Project Separation**: Users can only access projects they're members of
2. **Data Isolation**: No cross-project data access
3. **Role Flexibility**: Different roles in different projects
4. **Membership Control**: MANAGER-only member management

### Maintained Features:
1. **Admin Cross-Access**: Admins still have full access with admin tokens
2. **JWT Security**: Token-based authentication unchanged
3. **Swagger Integration**: All authentication methods work in Swagger UI

## Breaking Changes

### For API Clients:
1. **Project Access**: Must be project member to access project resources
2. **Global Endpoints**: Some global artifact/document endpoints deprecated
3. **Role Checks**: No more global role validation - use project membership
4. **User Creation**: New users have no global roles by default

### For Frontend Applications:
1. **Project Lists**: Only shows user's projects (not all projects)
2. **Permission Checks**: Must check project-specific permissions
3. **Member Management**: New UI needed for project member management
4. **Role Display**: Show project roles instead of global roles

## Migration Steps Completed

### ✅ Phase 1: Model Updates
- [x] Removed global UserRole enum from User model
- [x] Added ProjectMember model with project-specific roles
- [x] Updated User model with project permission methods
- [x] Added proper database relationships

### ✅ Phase 2: API Updates  
- [x] Updated all project endpoints with membership validation
- [x] Updated artifact endpoints with project-based permissions
- [x] Updated file endpoints with project membership checks
- [x] Updated document version endpoints with project validation
- [x] Added project member management endpoints

### ✅ Phase 3: Authorization Refactor
- [x] Replaced global permission patterns with project membership checks
- [x] Updated all `require_permissions()` calls to project validation
- [x] Removed `get_roles()` and `has_permission()` function calls
- [x] Implemented project-specific authorization decorators

### ✅ Phase 4: Cleanup
- [x] Removed deprecated RBAC files
- [x] Removed global permission system files  
- [x] Updated seed data to project-based system
- [x] Created comprehensive documentation

## Testing Verification

### ✅ Completed Tests:
- [x] Import validation - All modules import successfully
- [x] Database reset - Seeding works with new system
- [x] Project creation - Users automatically become MANAGER
- [x] Permission isolation - Non-members cannot access projects

### 🧪 Recommended Additional Testing:

#### 1. Project Membership Workflow:
- Login as user1 (MANAGER) 
- Add user2 as TESTER to project
- Login as user2 - verify can modify content but not delete
- Add user3 as VIEWER to project  
- Login as user3 - verify read-only access

#### 2. Permission Boundary Testing:
- Try accessing project as non-member (should fail)
- Try member management as TESTER (should fail)
- Try content deletion as VIEWER (should fail)
- Verify admin tokens still bypass all restrictions

#### 3. Cross-Project Isolation:
- Create multiple projects with different memberships
- Verify users only see their assigned projects
- Verify no cross-project data access

## Documentation Created

### 📚 New Documentation Files:

1. **`docs/project-based-authorization.md`**
   - Complete system architecture overview
   - Role definitions and permissions matrix  
   - Database models and relationships
   - Implementation guide with code examples
   - Migration summary and security considerations

2. **`docs/project-member-api.md`**
   - Detailed API documentation for project member management
   - Request/response examples with cURL, Python, JavaScript
   - Error codes and troubleshooting guide
   - Business rules and rate limiting information

3. **`docs/authorization-system.md` (Updated)**
   - Updated main authorization documentation
   - Reflects new project-based system
   - Maintains admin cross-access documentation
   - Updated usage examples and test scenarios

## System Status

### 🎯 **MIGRATION COMPLETE**

The system has been successfully migrated from a global role-based system to a project-based authorization system. Key achievements:

✅ **Full Project Isolation**: Users can only access projects they're members of  
✅ **Granular Permissions**: Role-based permissions within each project  
✅ **Backward Compatibility**: Admin system unchanged with full cross-access  
✅ **Security Enhanced**: Better data isolation and access control  
✅ **Scalability Improved**: No global permission conflicts  
✅ **Documentation Complete**: Comprehensive guides for developers and users  

### 🚀 **Ready for Production**

The system is now ready for production use with:
- Complete project-based authorization
- Comprehensive API documentation  
- Proper seeded test data
- Full admin cross-access maintained
- Enhanced security and isolation

### 📞 **Next Steps for Development Team**

1. **Frontend Updates**: Update UI to use new project member management APIs
2. **Integration Testing**: Test with real-world usage scenarios
3. **Performance Testing**: Validate project membership query performance
4. **User Training**: Update user guides for new project-based workflow
