# Authorization System Documentation

## Overview

This application implements a **project-based authorization system** with separate authentication models for **Admins** and **Users**. The system moved from global user roles to project-specific role assignments, providing better isolation and granular access control.

## System Architecture

### Two-Tier Authentication Model

1. **Admin System** - Full-access administrative control (unchanged)
2. **User System** - **NEW: Project-based roles with no global permissions**

## Admin Authorization System (Unchanged)

### Admin Model (Simplified)

All authenticated admins have **full access to all admin APIs and user APIs**. There are no role restrictions for admins.

#### Admin Features:
- **Simple Authentication**: Any authenticated admin can access all endpoints
- **Cross-System Access**: Admin tokens work on both admin and user APIs with full privileges
- **No Role Hierarchy**: All admins are equal with complete system privileges
- **Full System Access**: Admins can manage users, projects, and all system resources

#### Default Admin Accounts:
```
Admin 1:
- Email: admin@example.com
- Password: admin123
- Access: Full administrative access

Admin 2: 
- Email: admin2@example.com
- Password: admin123
- Access: Full administrative access
```

## ✨ **NEW: Project-Based User Authorization System**

### Key Changes

❌ **REMOVED**:
- Global user roles (MANAGER, TESTER, VIEWER)
- UserRole enum and global permission system
- `has_permission()` and `get_roles()` functions
- Global RBAC system

✅ **NEW**:
- Project-specific role assignments
- Fixed project roles: **MANAGER**, **TESTER**, **VIEWER**
- Project membership-based permissions
- Complete project isolation

### Project-Based Role System

Users now have **no global roles**. All permissions are granted through **project membership** with specific roles within each project.

#### Project Roles

| Role | Project Permissions | Description |
|------|-------------------|-------------|
| **MANAGER** | Full Control | Can manage project content, members, and settings |
| **TESTER** | Content Modification | Can create/update test artifacts and content |
| **VIEWER** | Read-Only | Can view project content but not modify |

### Permission Matrix (Project-Scoped)

| Operation | MANAGER | TESTER | VIEWER | Non-Member |
|-----------|---------|--------|--------|------------|
| **Project Access** |
| View project | ✅ | ✅ | ✅ | ❌ |
| Update project | ✅ | ❌ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ | ❌ |
| **Member Management** |
| Add members | ✅ | ❌ | ❌ | ❌ |
| Remove members | ✅ | ❌ | ❌ | ❌ |
| Change roles | ✅ | ❌ | ❌ | ❌ |
| **Content Management** |
| Create artifacts | ✅ | ✅ | ❌ | ❌ |
| Update artifacts | ✅ | ✅ | ❌ | ❌ |
| Delete artifacts | ✅ | ❌ | ❌ | ❌ |
| Upload files | ✅ | ✅ | ❌ | ❌ |
| **Document Versions** |
| Create versions | ✅ | ✅ | ❌ | ❌ |
| Update versions | ✅ | ✅ | ❌ | ❌ |
| Delete versions | ✅ | ❌ | ❌ | ❌ |
| **Chat Functions** |
| Create chat sessions | ✅ | ✅ | ✅ | ❌ |
| Send messages | ✅ | ✅ | ✅ | ❌ |
| AI generation | ✅ | ✅ | ✅ | ❌ |

### Default User Accounts (Updated):
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

## API Endpoints

### Admin API Endpoints (Unchanged):
```
POST   /api/v1/admin/register       - Register first admin (public)
POST   /api/v1/admin/login          - Admin login (OAuth2)
GET    /api/v1/admin/whoami         - Get current admin info
GET    /api/v1/admin/profile        - Get admin profile
GET    /api/v1/admin/all            - List all admins
POST   /api/v1/admin/create         - Create new admin
GET    /api/v1/admin/users/all      - Manage all users
POST   /api/v1/admin/users/create   - Create new user
PUT    /api/v1/admin/users/{id}     - Update any user
DELETE /api/v1/admin/users/{id}     - Delete any user
```

### User API Endpoints (Updated Authorization):

#### Authentication:
```
POST   /api/v1/users/login          - User login (OAuth2)
GET    /api/v1/users/whoami         - Get current user info
GET    /api/v1/users/me             - Get own profile
PUT    /api/v1/users/me/profile     - Update own profile
```

#### Project Management:
```
POST   /api/v1/projects/            - Create project (Any user - becomes MANAGER)
GET    /api/v1/projects/            - List user's projects (Member only)
GET    /api/v1/projects/{id}        - Get project (Member only)
PUT    /api/v1/projects/{id}        - Update project (MANAGER only)
DELETE /api/v1/projects/{id}        - Delete project (MANAGER only)
```

#### **NEW: Project Member Management:**
```
GET    /api/v1/projects/{id}/members              - List project members
POST   /api/v1/projects/{id}/members              - Add member (MANAGER only)
PUT    /api/v1/projects/{id}/members/{user_id}    - Update member role (MANAGER only)
DELETE /api/v1/projects/{id}/members/{user_id}    - Remove member (MANAGER only)
POST   /api/v1/projects/{id}/members/bulk         - Add multiple members (MANAGER only)
GET    /api/v1/project-roles                      - Get available roles
```

#### Project-Scoped Resources:
```
# All endpoints now require project membership
GET    /api/v1/project-artifacts/project/{id}     - Get project artifacts (Member only)
POST   /api/v1/project-artifacts/                 - Create artifact (MANAGER/TESTER only)
PUT    /api/v1/project-artifacts/{id}            - Update artifact (MANAGER/TESTER only)  
DELETE /api/v1/project-artifacts/{id}            - Delete artifact (MANAGER only)

GET    /api/v1/projects/{id}/files               - List files (Member only)
POST   /api/v1/projects/{id}/files/{path}        - Upload file (MANAGER/TESTER only)
PUT    /api/v1/projects/{id}/files/{path}        - Update file (MANAGER/TESTER only)
DELETE /api/v1/projects/{id}/files/{path}        - Delete file (MANAGER only)

POST   /api/v1/chat/sessions                     - Create chat (Member only)
GET    /api/v1/chat/sessions/{id}                - Get chat (Member only)
```

## Implementation Details

### Authentication Flow (Updated)

#### User Authentication:
1. POST to `/api/v1/users/login` with credentials  
2. Receive JWT token with `"type": "user"`
3. Use token in `Authorization: Bearer <token>` header
4. **NEW**: Each endpoint validates project membership + role permissions

### Permission Validation (Updated)

#### Project-Based Authorization:
```python
# NEW: Project membership validation
current_user: User = Depends(get_current_user)

# Check project membership
if not current_user.is_project_member(project_id):
    raise HTTPException(403, "Access denied: Not a project member")

# Check role-specific permissions
if not current_user.can_modify_project_content(project_id):
    raise HTTPException(403, "Insufficient permissions to modify content")

# Check manager-only operations
if not current_user.can_manage_project_members(project_id):
    raise HTTPException(403, "Only project managers can manage members")
```

#### User Model Methods (NEW):
```python
class User:
    def is_project_member(self, project_id: uuid.UUID) -> bool:
        """Check if user is a member of the project"""
        
    def get_project_role(self, project_id: uuid.UUID) -> Optional[ProjectRole]:
        """Get user's role in a specific project"""
        
    def can_modify_project_content(self, project_id: uuid.UUID) -> bool:
        """Check if user can modify project content (MANAGER/TESTER)"""
        
    def can_manage_project_members(self, project_id: uuid.UUID) -> bool:
        """Check if user can manage project members (MANAGER only)"""
```

### Database Schema (Updated)

#### User Model (Simplified):
```python
class User(SQLModel, table=True):
    id: uuid.UUID (Primary Key)
    username: str (Unique)
    email: str (Unique)
    full_name: Optional[str]
    # REMOVED: roles field
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    # NEW: Project memberships relationship
    project_memberships: List["ProjectMember"] = Relationship(...)
```

#### **NEW: ProjectMember Model**:
```python
class ProjectMember(SQLModel, table=True):
    project_id: uuid.UUID (FK to Project, Primary Key)
    user_id: uuid.UUID (FK to User, Primary Key)
    role: ProjectRole (MANAGER, TESTER, VIEWER)
    is_active: bool = True
    joined_at: datetime
    added_by: Optional[uuid.UUID]
    updated_at: datetime
    updated_by: Optional[uuid.UUID]
```

## Usage Examples (Updated)

### Project Creation and Management:
```bash
# User login
curl -X POST "/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=user123"

# Create project (user becomes MANAGER automatically)
curl -X POST "/api/v1/projects/" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Project", "note": "Test project"}'

# Add member to project (MANAGER only)
curl -X POST "/api/v1/projects/{project_id}/members" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user2_uuid", "role": "TESTER"}'
```

### Permission Testing:
```bash
# Try to access project as non-member (should fail)
curl -X GET "/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <non_member_token>"
# Expected: 403 Forbidden

# Try to delete artifact as TESTER (should fail)  
curl -X DELETE "/api/v1/project-artifacts/{artifact_id}" \
  -H "Authorization: Bearer <tester_token>"
# Expected: 403 Forbidden

# Try to add member as VIEWER (should fail)
curl -X POST "/api/v1/projects/{project_id}/members" \
  -H "Authorization: Bearer <viewer_token>" \
  -d '{"user_id": "user_uuid", "role": "TESTER"}'
# Expected: 403 Forbidden
```

## Migration Summary

### What Was Removed:
- ❌ Global user roles (`roles` field in User model)
- ❌ UserRole enum (MANAGER, TESTER, VIEWER as global roles)
- ❌ Global permission system (`has_permission()`, `get_roles()`)
- ❌ RBAC dynamic role system
- ❌ Global access to projects/resources

### What Was Added:
- ✅ Project-specific role assignments
- ✅ ProjectMember model for membership management
- ✅ Project membership validation in all APIs
- ✅ User model methods for project-based permissions
- ✅ Project member management APIs
- ✅ Complete project isolation

### Benefits of New System:
1. **Better Isolation**: Users can only access projects they're members of
2. **Granular Control**: Different roles in different projects
3. **Scalability**: No global permission conflicts
4. **Security**: Complete separation between projects
5. **Flexibility**: Users can have different roles in different projects

## Testing the New System

### Test Scenarios:

#### 1. Project Isolation:
- Login as user1 → Should only see projects where user1 is a member
- Try to access user2's project → Should return 403 Forbidden
- Create new project → user1 automatically becomes MANAGER

#### 2. Role-Based Permissions:
- Add user2 as TESTER to project → user2 can create/update artifacts
- Add user3 as VIEWER to project → user3 can only read content
- Try VIEWER creating artifact → Should return 403 Forbidden

#### 3. Member Management:
- MANAGER can add/remove members → Should succeed
- TESTER tries to add member → Should return 403 Forbidden
- Remove last MANAGER → Should be prevented

#### 4. Admin Cross-Access (Still Works):
- Admin token on user APIs → Should bypass all project restrictions
- Admin can access any project → Should succeed regardless of membership

### Swagger UI Testing:

1. **Navigate to**: `http://127.0.0.1:8000/docs`

2. **Test Project-Based Access**:
   - Login as `user1` → See "Sample Testing Project"
   - Login as `user2` → See no projects initially
   - Use user1 to add user2 to project → user2 can now access it

3. **Test Role Restrictions**:
   - Login as MANAGER → Try all operations (should work)
   - Login as TESTER → Try delete operations (should fail)  
   - Login as VIEWER → Try create operations (should fail)

This new project-based authorization system provides complete project isolation while maintaining the admin system's cross-access capabilities.
