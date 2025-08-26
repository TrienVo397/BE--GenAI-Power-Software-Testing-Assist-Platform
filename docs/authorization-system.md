# Authorization System Documentation

## Overview

The GenAI Power Software Testing Assist Platform implements a **dual authorization system** with:

1. **Admin System**: Simple, full-access administrative control
2. **User System**: Project-based role assignments with complete project isolation

## System Architecture

### Dual Authentication Model

- **Admin Authentication**: Full system access with simple credential-based auth
- **User Authentication**: Project-scoped permissions with membership-based access control

---

## Admin Authorization System

### Admin Model

**All authenticated admins have full system access.** There are no role restrictions or hierarchies for admins.

#### Admin Features:
- **Universal Access**: Any authenticated admin can access all admin and user APIs
- **Cross-System Tokens**: Admin tokens work across both admin and user endpoint systems
- **No Role Restrictions**: All admins have identical, complete system privileges
- **Full User Management**: Admins can create, modify, and delete any user or project

#### Admin Authentication Flow:
```http
POST /api/v1/admin/login
{
  "admin_username": "admin",
  "password": "admin123"
}

# Returns admin token with full system access
# Token works on both /api/v1/admin/* and /api/v1/users/* endpoints
```

#### Default Admin Accounts:
```
Admin 1:
- Username: admin
- Email: admin@example.com
- Password: admin123
- Access: Full administrative access

Admin 2: 
- Username: admin2
- Email: admin2@example.com
- Password: admin123
- Access: Full administrative access
```

---

## Project-Based User Authorization System

### Core Architecture

Users have **no global roles or permissions**. All user access is controlled through:
- **Project Membership**: Users must be members of projects to access them
- **Project Roles**: Three fixed roles with specific permissions within projects
- **Complete Isolation**: Users cannot access projects where they are not members

### Project Roles

The system uses **three fixed project roles**:

| Role | Level | Description |
|------|-------|-------------|
| **MANAGER** | High | Full project control including member management |
| **TESTER** | Medium | Can create and modify project content and test artifacts |
| **VIEWER** | Low | Read-only access to project content |

### Permission Matrix

| Operation | MANAGER | TESTER | VIEWER | Non-Member |
|-----------|---------|--------|--------|------------|
| **Project Access** |
| View project details | ✅ | ✅ | ✅ | ❌ |
| View project content | ✅ | ✅ | ✅ | ❌ |
| Update project settings | ✅ | ❌ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ | ❌ |
| **Member Management** |
| Add project members | ✅ | ❌ | ❌ | ❌ |
| Remove project members | ✅ | ❌ | ❌ | ❌ |
| Change member roles | ✅ | ❌ | ❌ | ❌ |
| **Content Management** |
| Create artifacts | ✅ | ✅ | ❌ | ❌ |
| Update artifacts | ✅ | ✅ | ❌ | ❌ |
| Delete artifacts | ✅ | ❌ | ❌ | ❌ |
| Upload/manage files | ✅ | ✅ | ❌ | ❌ |
| **Document Versions** |
| Create versions | ✅ | ✅ | ❌ | ❌ |
| Update versions | ✅ | ✅ | ❌ | ❌ |
| Delete versions | ✅ | ❌ | ❌ | ❌ |
| **Chat & AI Functions** |
| Create chat sessions | ✅ | ✅ | ✅ | ❌ |
| Send chat messages | ✅ | ✅ | ✅ | ❌ |
| Use AI generation | ✅ | ✅ | ✅ | ❌ |
| **Bot Operations** |
| Run coverage analysis | ✅ | ✅ | ✅ | ❌ |

### User Authentication Flow:
```http
POST /api/v1/users/login
{
  "username": "user1",
  "password": "user123"
}

# Returns user token
# Token only grants access to projects where user is a member
```

### Default User Accounts:
```
User 1:
- Username: user1
- Email: user1@example.com
- Password: user123
- Project Membership: MANAGER of "Sample Testing Project"

User 2:
- Username: user2
- Email: user2@example.com  
- Password: user123
- Project Membership: None (no project access)

User 3:
- Username: user3
- Email: user3@example.com
- Password: user123
- Project Membership: None (no project access)
```

---

## API Endpoints

### Admin API Endpoints

#### Admin Authentication & Profile:
```
POST   /api/v1/admin/register       - Register first admin (public, one-time)
POST   /api/v1/admin/login          - Admin login (returns admin token)
GET    /api/v1/admin/whoami         - Get current admin info
GET    /api/v1/admin/profile        - Get admin profile details
```

#### Admin Management (Full Access):
```
GET    /api/v1/admin/all            - List all admins
POST   /api/v1/admin/create         - Create new admin
PUT    /api/v1/admin/{id}           - Update admin details
DELETE /api/v1/admin/{id}           - Delete admin
```

#### User Management via Admin (Full Access):
```
GET    /api/v1/admin/users/all      - List all users
POST   /api/v1/admin/users/create   - Create new user
PUT    /api/v1/admin/users/{id}     - Update any user
DELETE /api/v1/admin/users/{id}     - Delete any user
```

#### Project Management via Admin (Full Access):
```
GET    /api/v1/admin/projects/all   - List all projects
POST   /api/v1/admin/projects       - Create project
PUT    /api/v1/admin/projects/{id}  - Update any project
DELETE /api/v1/admin/projects/{id}  - Delete any project
```

### User API Endpoints

#### User Authentication & Profile:
```
POST   /api/v1/users/register       - User registration (public)
POST   /api/v1/users/login          - User login (returns user token)
GET    /api/v1/users/whoami         - Get current user info
GET    /api/v1/users/me             - Get own profile
PUT    /api/v1/users/me/profile     - Update own profile
```

#### Project Management (Membership Required):
```
POST   /api/v1/projects/            - Create project (creator becomes MANAGER)
GET    /api/v1/projects/            - List user's projects (member projects only)
GET    /api/v1/projects/{id}        - Get project details (members only)
PUT    /api/v1/projects/{id}        - Update project (MANAGER only)
DELETE /api/v1/projects/{id}        - Delete project (MANAGER only)
```

#### Project Member Management (MANAGER Only):
```
GET    /api/v1/projects/{id}/members              - List project members
POST   /api/v1/projects/{id}/members              - Add member to project
PUT    /api/v1/projects/{id}/members/{user_id}    - Update member role
DELETE /api/v1/projects/{id}/members/{user_id}    - Remove member
POST   /api/v1/projects/{id}/members/bulk         - Add multiple members
GET    /api/v1/project-roles                      - List available project roles
```

#### Project Content (Role-Based Access):
```
# Project Artifacts (Members only, MANAGER/TESTER can modify)
GET    /api/v1/project-artifacts/project/{id}     - Get project artifacts
POST   /api/v1/project-artifacts/                 - Create artifact (MANAGER/TESTER)
PUT    /api/v1/project-artifacts/{id}            - Update artifact (MANAGER/TESTER)
DELETE /api/v1/project-artifacts/{id}            - Delete artifact (MANAGER only)

# File Management (Members only, MANAGER/TESTER can modify)
GET    /api/v1/projects/{id}/files               - List project files
POST   /api/v1/projects/{id}/files/{path}        - Upload file (MANAGER/TESTER)
PUT    /api/v1/projects/{id}/files/{path}        - Update file (MANAGER/TESTER)
DELETE /api/v1/projects/{id}/files/{path}        - Delete file (MANAGER only)

# Document Versions (Members only, MANAGER/TESTER can modify)
GET    /api/v1/document-versions/project/{id}    - Get document versions
POST   /api/v1/document-versions/                - Create version (MANAGER/TESTER)
PUT    /api/v1/document-versions/{id}            - Update version (MANAGER/TESTER)
DELETE /api/v1/document-versions/{id}            - Delete version (MANAGER only)
```

#### Chat System (Project-Scoped):
```
# All chat operations require project membership
POST   /api/v1/chat/sessions        - Create chat session (requires project_id)
GET    /api/v1/chat/sessions        - List user's chat sessions (project-filtered)
GET    /api/v1/chat/sessions/{id}   - Get chat session (member verification)
POST   /api/v1/chat/sessions/{id}/messages - Send message (member verification)
```

#### Bot Operations (Project-Scoped):
```
# Bot operations require project membership
POST   /api/v1/bot/coverage-test    - Run coverage analysis (members only)
```

---

## Implementation Details

### Permission Validation Flow

#### Project-Based Authorization (Users):
```python
# 1. Validate user token
current_user: User = Depends(get_current_user)

# 2. Extract project_id from request (path param, body, or query)
project_id: uuid.UUID = # from request

# 3. Validate project membership
if not current_user.is_project_member(project_id):
    raise HTTPException(403, "Access denied: Not a project member")

# 4. Check role-specific permissions (if needed)
if operation_requires_modification:
    if not current_user.can_modify_project_content(project_id):
        raise HTTPException(403, "Insufficient permissions")

# 5. Check manager-only operations (if needed)
if operation_requires_management:
    if not current_user.can_manage_project_members(project_id):
        raise HTTPException(403, "Only project managers can perform this action")
```

#### Admin Authorization (Admins):
```python
# 1. Validate admin token
current_admin: Admin = Depends(get_current_admin)

# 2. No further authorization needed - admin has full access
# Proceed with operation
```

#### Cross-Token Support:
```python
# Admin tokens work on user endpoints with full privileges
# User tokens only work on user endpoints with project restrictions
@router.get("/api/v1/projects/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user_or_admin)  # Special dependency
):
    # If admin token: bypass all project restrictions
    # If user token: enforce project membership
    pass
```

### Database Models

#### User Model (Simplified):
```python
class User(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project_memberships: List["ProjectMember"] = Relationship(back_populates="user")
    
    # Project-based permission methods
    def is_project_member(self, project_id: uuid.UUID) -> bool:
        """Check if user is a member of the specific project"""
        return any(
            membership.project_id == project_id and membership.is_active
            for membership in self.project_memberships
        )
    
    def get_project_role(self, project_id: uuid.UUID) -> Optional[ProjectRole]:
        """Get user's role in the specific project"""
        for membership in self.project_memberships:
            if membership.project_id == project_id and membership.is_active:
                return membership.role
        return None
    
    def can_modify_project_content(self, project_id: uuid.UUID) -> bool:
        """Check if user can modify project content (MANAGER/TESTER only)"""
        role = self.get_project_role(project_id)
        return role in [ProjectRole.MANAGER, ProjectRole.TESTER]
    
    def can_manage_project_members(self, project_id: uuid.UUID) -> bool:
        """Check if user can manage project members (MANAGER only)"""
        role = self.get_project_role(project_id)
        return role == ProjectRole.MANAGER
```

#### ProjectMember Model:
```python
class ProjectMember(SQLModel, table=True):
    project_id: uuid.UUID = Field(foreign_key="project.id", primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    role: ProjectRole = Field()  # MANAGER, TESTER, VIEWER
    is_active: bool = True
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[uuid.UUID] = Field(foreign_key="user.id")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[uuid.UUID] = Field(foreign_key="user.id")
    
    # Relationships
    project: "Project" = Relationship(back_populates="members")
    user: "User" = Relationship(back_populates="project_memberships")
```

#### Admin Model (Simple):
```python
class Admin(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    admin_username: str = Field(unique=True, index=True)
    admin_email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # No roles or permission fields - all admins have full access
```

---

## Usage Examples

### Admin Operations:
```bash
# Admin login
curl -X POST "/api/v1/admin/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "admin_username=admin&password=admin123"

# Create user (admin can create users directly)
curl -X POST "/api/v1/admin/users/create" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com", 
    "password": "newuser123",
    "full_name": "New User"
  }'

# Access any project (admin bypass)
curl -X GET "/api/v1/projects/{any_project_id}" \
  -H "Authorization: Bearer <admin_token>"
```

### User Project Management:
```bash
# User login
curl -X POST "/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=user123"

# Create project (user becomes MANAGER automatically)
curl -X POST "/api/v1/projects/" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My New Project",
    "note": "Project for testing"
  }'

# Add member to project (MANAGER only)
curl -X POST "/api/v1/projects/{project_id}/members" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user2_id}",
    "role": "TESTER"
  }'

# Run coverage analysis (requires project membership)
curl -X POST "/api/v1/bot/coverage-test" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "{project_id}"
  }'
```

### Permission Testing:
```bash
# Try to access project as non-member (should fail)
curl -X GET "/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <non_member_token>"
# Expected: 403 Forbidden - Not a project member

# Try to delete artifact as VIEWER (should fail)  
curl -X DELETE "/api/v1/project-artifacts/{artifact_id}" \
  -H "Authorization: Bearer <viewer_token>"
# Expected: 403 Forbidden - Insufficient permissions

# Try to add member as TESTER (should fail)
curl -X POST "/api/v1/projects/{project_id}/members" \
  -H "Authorization: Bearer <tester_token>" \
  -d '{"user_id": "{user_id}", "role": "VIEWER"}'
# Expected: 403 Forbidden - Only managers can manage members
```

---

## Security Features

### Project Isolation:
- **Complete Separation**: Users can only see and access projects they are members of
- **No Cross-Project Access**: Users cannot access resources from projects they don't belong to
- **Role Enforcement**: All operations check both membership and role permissions

### Admin Security:
- **Separate Authentication**: Admin and user systems use different login endpoints
- **Full Access Control**: Admin tokens bypass all project restrictions
- **Cross-System Compatibility**: Admin tokens work on both admin and user APIs

### Audit & Compliance:
- **Membership Tracking**: All project memberships track who added/modified them
- **Role Changes**: Role updates are logged with timestamps and modifying user
- **Project Creation**: Project creators are automatically assigned as managers

---

## Testing the System

### Swagger UI Testing:

1. **Navigate to**: `http://127.0.0.1:8000/docs`

2. **Test Admin Access**:
   - Login as admin → Full access to all endpoints
   - Access any project → Should succeed regardless of membership
   - Manage any user or project → Should succeed

3. **Test User Project Isolation**:
   - Login as user1 → Should only see "Sample Testing Project"
   - Login as user2 → Should see no projects initially
   - Try to access user1's project as user2 → Should fail with 403

4. **Test Role-Based Permissions**:
   - Add user2 as TESTER to project via user1 (MANAGER)
   - Login as user2 → Should now see the project
   - Try to add member as user2 (TESTER) → Should fail with 403
   - Try to create artifact as user2 (TESTER) → Should succeed

5. **Test Chat and Bot Integration**:
   - Create chat session → Requires project_id and membership
   - Run coverage analysis → Requires project membership
   - Access chat sessions → Only shows sessions from user's projects

### Common Test Scenarios:

1. **Project Creation Flow**:
   - Any user can create a project
   - Creator automatically becomes MANAGER
   - Other users cannot see the project until added

2. **Member Management Flow**:
   - Only MANAGER can add/remove members
   - MANAGER can assign any role (MANAGER, TESTER, VIEWER)
   - Members can see project but permissions vary by role

3. **Content Access Flow**:
   - All members can view project content
   - MANAGER and TESTER can modify content
   - Only MANAGER can delete content
   - VIEWER has read-only access

This authorization system ensures complete project isolation while maintaining administrative oversight capabilities.
