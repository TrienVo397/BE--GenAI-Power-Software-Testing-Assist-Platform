# Authorization System Documentation

## Overview

This application implements a dual-tier authorization system with separate authentication and permission models for **Admins** and **Users**. The system is designed to provide clear separation of concerns between administrative functions and regular user operations.

## System Architecture

### Two-Tier Authentication Model

1. **Admin System** - Simplified full-access administrative control
2. **User System** - Role-based permissions with granular access control

## Admin Authorization System

### Admin Model (Simplified)

All authenticated admins have **full access to all admin APIs**. There are no role restrictions or permission hierarchies for admins.

#### Admin Features:
- **Simple Authentication**: Any authenticated admin can access all admin endpoints
- **No Role Hierarchy**: All admins are equal with complete administrative privileges  
- **Full System Access**: Admins can manage users, projects, and all system resources
- **OAuth2 Compatible**: Works with Swagger UI authentication at `/api/v1/admin/login`

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

## ✅ Complete API Coverage with Permission Checks

Based on comprehensive analysis of all API endpoints, here's the complete list of APIs and their permission requirements:

#### Admin API Endpoints:
```
POST   /api/v1/admin/register       - Register first admin (public)
POST   /api/v1/admin/login          - Admin login (OAuth2)
GET    /api/v1/admin/whoami         - Get current admin info
GET    /api/v1/admin/profile        - Get admin profile
GET    /api/v1/admin/all            - List all admins
GET    /api/v1/admin/{admin_id}     - Get admin by ID
POST   /api/v1/admin/create         - Create new admin
PUT    /api/v1/admin/{admin_id}     - Update admin
GET    /api/v1/admin/users/all      - Manage all users
POST   /api/v1/admin/users/create   - Create new user
PUT    /api/v1/admin/users/{id}     - Update any user
DELETE /api/v1/admin/users/{id}     - Delete any user
```

**Note**: All admin endpoints require admin authentication via JWT token from `/api/v1/admin/login`

#### ✨ **NEW: Admin Cross-Access Feature**
**Admins can now access ALL user APIs with full privileges!**

When an admin logs in through `/api/v1/admin/login` and gets an admin JWT token, they can use that same token to access any user API endpoint with unlimited permissions. This provides system administrators with complete oversight and management capabilities.

**Example Admin Cross-Access:**
```bash
# Admin login
curl -X POST "/api/v1/admin/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Use admin token to access user APIs (full access granted)
curl -X POST "/api/v1/projects/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Admin Project", "meta_data": {}, "note": "Created by admin"}'

curl -X DELETE "/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <admin_token>"
  # ✅ Admin can delete even though they don't have "Manager" role
```

### 🔗 **Swagger UI Cross-Token Support**

The Swagger UI at `/docs` now supports **cross-token authentication**, allowing admins to seamlessly test user APIs with admin privileges:

#### Features:
- **Dual Authentication Options**: Swagger UI shows both "AdminOAuth2PasswordBearer" and "UserOAuth2PasswordBearer" authentication options
- **Cross-Token Compatibility**: Admin tokens work on user API endpoints through Swagger UI
- **Smart Token Detection**: System automatically detects token type and applies appropriate authorization
- **Enhanced Testing**: Admins can test any user API endpoint using their admin credentials

#### How to Use Cross-Token in Swagger:

1. **Navigate to Swagger UI**: Go to `http://127.0.0.1:8000/docs`

2. **Admin Testing (Recommended for Full Access)**:
   - Click "Authorize" button in Swagger UI
   - Choose "AdminOAuth2PasswordBearer" 
   - Enter admin credentials: `admin@example.com` / `admin123`
   - Click "Authorize"
   - **Result**: Admin token now works on ALL user API endpoints with full privileges

3. **User Testing (Role-Based Access)**:
   - Click "Authorize" button in Swagger UI  
   - Choose "UserOAuth2PasswordBearer"
   - Enter user credentials (manager/tester/viewer)
   - Click "Authorize"
   - **Result**: User token follows role-based permission restrictions

4. **Cross-Token Benefits**:
   ```
   ✅ Admin login → Test user APIs with full access (no role restrictions)
   ✅ User login → Test user APIs with role-based permissions  
   ✅ Seamless switching between authentication types
   ✅ Consistent behavior between Swagger UI and API calls
   ```

#### Swagger Security Configuration:
The OpenAPI schema automatically configures both authentication schemes for all protected endpoints:
```yaml
security:
  - UserOAuth2PasswordBearer: []  # Standard user authentication
  - AdminOAuth2PasswordBearer: [] # Admin authentication with cross-access
```

---

## User Authorization System

### Role-Based Access Control (RBAC)

The user system implements a comprehensive role-based permission model with three distinct roles:

#### 1. **Manager Role** 
- **Full Access**: Complete CRUD operations on all resources
- **User Management**: Can create, read, update, and delete other users
- **Project Management**: Full project lifecycle management
- **Document Management**: Complete document version control
- **Artifact Management**: Full artifact lifecycle management
- **File Management**: Full file and directory management
- **Permission Level**: ALL operations (CREATE, READ, UPDATE, DELETE)

#### 2. **Tester Role**
- **Limited Access**: Full access except DELETE operations
- **Testing Operations**: Can create and modify test artifacts
- **Project Collaboration**: Can create and update projects
- **Document Management**: Can create and update document versions
- **File Management**: Can upload/update files but not delete them
- **Permission Level**: CREATE, READ, UPDATE (no DELETE)

#### 3. **Viewer Role**
- **Read-Only Access**: Can only view and read existing resources
- **No Modifications**: Cannot create, update, or delete anything
- **Information Access**: Can browse projects, documents, artifacts, and files
- **Permission Level**: READ only

### Default User Accounts:
```
Manager:
- Email: manager@example.com
- Password: manager123
- Role: MANAGER
- Access: Full CRUD operations

Tester:
- Email: tester@example.com  
- Password: tester123
- Role: TESTER
- Access: CREATE, READ, UPDATE (no DELETE)

Viewer:
- Email: viewer@example.com
- Password: viewer123
- Role: VIEWER  
- Access: READ only
```

### Permission Matrix

| Resource | Manager | Tester | Viewer |
|----------|---------|---------|--------|
| **Users** |
| Create Users | ✅ | ❌ | ❌ |
| Read Users | ✅ | ✅ | ✅ |
| Update Users | ✅ | ❌ | ❌ |
| Delete Users | ✅ | ❌ | ❌ |
| **Projects** |
| Create Projects | ✅ | ✅ | ❌ |
| Read Projects | ✅ | ✅ | ✅ |
| Update Projects | ✅ | ✅ | ❌ |
| Delete Projects | ✅ | ❌ | ❌ |
| **Documents** |
| Create Documents | ✅ | ✅ | ❌ |
| Read Documents | ✅ | ✅ | ✅ |
| Update Documents | ✅ | ✅ | ❌ |
| Delete Documents | ✅ | ❌ | ❌ |
| **Artifacts** |
| Create Artifacts | ✅ | ✅ | ❌ |
| Read Artifacts | ✅ | ✅ | ✅ |
| Update Artifacts | ✅ | ✅ | ❌ |
| Delete Artifacts | ✅ | ❌ | ❌ |
| **Files** |
| List/Read Files | ✅ | ✅ | ✅ |
| Upload Files | ✅ | ✅ | ❌ |
| Update Files | ✅ | ✅ | ❌ |
| Delete Files | ✅ | ❌ | ❌ |
| Create Directories | ✅ | ✅ | ❌ |
| **Chat** |
| Create Chat Sessions | ✅ | ✅ | ❌ |
| Read Chat Sessions | ✅ | ✅ | ✅ |
| Update Chat Sessions | ✅ | ✅ | ❌ |
| Delete Chat Sessions | ✅ | ✅ | ❌ |
| Stream Messages | ✅ | ✅ | ❌ |

### User API Endpoints:

#### Authentication:
```
POST   /api/v1/users/register       - User registration (public)
POST   /api/v1/users/login          - User login (OAuth2)
GET    /api/v1/users/whoami         - Get current user info
```

#### User Management (Manager Only):
```
POST   /api/v1/users/create         - Create new user
GET    /api/v1/users/all            - List all users  
GET    /api/v1/users/{user_id}      - Get user by ID
PUT    /api/v1/users/{user_id}      - Update user
DELETE /api/v1/users/{user_id}      - Delete user
PUT    /api/v1/users/{user_id}/roles - Update user roles
```

#### Self-Service:
```
GET    /api/v1/users/me             - Get own profile
PUT    /api/v1/users/me/profile     - Update own profile
```

#### Project Management:
```
POST   /api/v1/projects/            - Create project (Manager/Tester)
GET    /api/v1/projects/            - List projects (All)
GET    /api/v1/projects/{id}        - Get project (All)
PUT    /api/v1/projects/{id}        - Update project (Manager/Tester)
DELETE /api/v1/projects/{id}        - Delete project (Manager only)
```

#### Document Management:
```
POST   /api/v1/document-versions/   - Create version (Manager/Tester)
GET    /api/v1/document-versions/{id} - Get version by ID (All)
GET    /api/v1/document-versions/project/{project_id} - Get project versions (All)
GET    /api/v1/document-versions/project/{project_id}/current - Get current version (All)
PUT    /api/v1/document-versions/{id} - Update version (Manager/Tester)
DELETE /api/v1/document-versions/{id} - Delete version (Manager only)
```

#### Artifact Management:
```
POST   /api/v1/project-artifacts/   - Create artifact (Manager/Tester)
GET    /api/v1/project-artifacts/   - List all artifacts (All)
GET    /api/v1/project-artifacts/{id} - Get artifact by ID (All)
GET    /api/v1/project-artifacts/project/{project_id} - Get project artifacts (All)
GET    /api/v1/project-artifacts/version/{version_id} - Get version artifacts (All)
GET    /api/v1/project-artifacts/type/{artifact_type} - Get artifacts by type (All)
PUT    /api/v1/project-artifacts/{id} - Update artifact (Manager/Tester)  
DELETE /api/v1/project-artifacts/{id} - Delete artifact (Manager only)
```

#### File Management:
```
GET    /api/v1/projects/{project_id}/files - List project files (All)
GET    /api/v1/projects/{project_id}/files/{file_path:path} - Get file (All)
GET    /api/v1/projects/{project_id}/files/{file_path:path}/info - Get file info (All)
POST   /api/v1/projects/{project_id}/files/{file_path:path} - Upload file (Manager/Tester)
PUT    /api/v1/projects/{project_id}/files/{file_path:path} - Update file text (Manager/Tester)
PUT    /api/v1/projects/{project_id}/files/{file_path:path}/upload - Update file upload (Manager/Tester)
DELETE /api/v1/projects/{project_id}/files/{file_path:path} - Delete file (Manager only)
POST   /api/v1/projects/{project_id}/directories/{directory_path:path} - Create directory (Manager/Tester)
```

#### Chat Management:
```
POST   /api/v1/chat/sessions        - Create chat session (Manager/Tester)
GET    /api/v1/chat/sessions        - List chat sessions (All)
GET    /api/v1/chat/sessions/{session_id} - Get chat session (All)
GET    /api/v1/chat/sessions/{session_id}/messages - Get session messages (All)
PUT    /api/v1/chat/sessions/{session_id} - Update chat session (Manager/Tester)
DELETE /api/v1/chat/sessions/{session_id} - Delete chat session (Manager/Tester)
PUT    /api/v1/chat/sessions/{session_id}/messages/{sequence_num} - Update message (Manager/Tester)
DELETE /api/v1/chat/sessions/{session_id}/messages/{sequence_num} - Delete message (Manager/Tester)
POST   /api/v1/chat/sessions/{session_id}/messages/stream - Stream chat messages (Manager/Tester)
```

---

## Implementation Details

### Authentication Flow

#### Admin Authentication:
1. POST to `/api/v1/admin/login` with credentials
2. Receive JWT token with `"type": "admin"`
3. Use token in `Authorization: Bearer <token>` header
4. Access all admin endpoints without additional permission checks

#### User Authentication:
1. POST to `/api/v1/users/login` with credentials  
2. Receive JWT token with `"type": "user"`
3. Use token in `Authorization: Bearer <token>` header
4. Each endpoint validates specific permissions based on user role

### Permission Validation

#### Admin Endpoints:
```python
# Simple admin authentication - no role checks needed
current_admin: Admin = Depends(get_current_admin)
```

#### User Endpoints:
```python
# Enhanced authorization dependency supports both user and admin tokens
current_user: User = Depends(require_permissions(Permission.PROJECT_CREATE))

# The system automatically detects:
# - User tokens: Apply role-based permission checks
# - Admin tokens: Grant full access (bypass permission checks)
```

#### Permission Validation Logic:
1. **Token Detection**: System determines if token is user or admin type
2. **Admin Path**: If admin token → Grant full access to all user APIs  
3. **User Path**: If user token → Apply role-based permission validation

```python
# Admin token example (full access)
if token_type == "admin":
    logger.info("Admin token detected - granting full access")
    return admin_user_object  # Bypass all permission checks

# User token example (role-based)  
elif token_type == "user":
    user_roles = current_user.get_roles()
    if not has_permission(user_roles, required_permission):
        raise HTTPException(403, "Insufficient permissions")
```

### Security Features

1. **Separated Token Types**: Admin and user tokens are distinct (`"type": "admin"` vs `"type": "user"`)
2. **Admin Cross-Access**: Admins can use their admin tokens to access user APIs with full privileges  
3. **OAuth2 Compliance**: Both systems work with Swagger UI authentication
4. **JWT Security**: Secure token-based authentication with expiration
5. **Permission Granularity**: Fine-grained control over resource access for users
6. **Self-Service Protection**: Users can only modify their own profiles  
7. **Admin Isolation**: Admin endpoints remain completely separate from user endpoints
8. **Dual Authentication**: System intelligently detects and processes both token types

### Database Schema

#### Admin Model (Simplified):
```python
class Admin(SQLModel, table=True):
    id: uuid.UUID (Primary Key)
    admin_username: str (Unique)
    admin_email: str (Unique)  
    full_name: Optional[str]
    department: Optional[str]
    notes: Optional[str]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    created_by: Optional[uuid.UUID]
    linked_user_id: Optional[uuid.UUID]
```

#### User Model:
```python
class User(SQLModel, table=True):
    id: uuid.UUID (Primary Key)
    username: str (Unique)
    email: str (Unique)
    full_name: Optional[str]
    roles: str  # JSON array: ["manager", "tester", "viewer"]
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
```

---

## Usage Examples

### Admin Operations:
```bash
# Admin login
curl -X POST "/api/v1/admin/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Create user (admin only)
curl -X POST "/api/v1/admin/users/create" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "new@example.com", "password": "pass123"}'
```

### User Operations:
```bash
# User login
curl -X POST "/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager&password=manager123"

# Create project (manager/tester only)
curl -X POST "/api/v1/projects/" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Project", "meta_data": {}, "note": "Test project"}'

# Try to delete project (manager only - will fail for tester/viewer)
curl -X DELETE "/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <user_token>"
```

---

## Error Handling

### Common HTTP Status Codes:

- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Authenticated but insufficient permissions
- **404 Not Found**: Resource does not exist
- **400 Bad Request**: Invalid input data

### Permission Error Examples:

#### Insufficient Permissions:
```json
{
  "detail": "Insufficient permissions. Only managers and testers can create projects."
}
```

#### Admin vs User Token Mismatch:
```json
{
  "detail": "Invalid admin token"
}
```

#### Role-Based Restrictions:
```json
{
  "detail": "Insufficient permissions. Only managers can delete projects."
}
```

---

## Security Best Practices

1. **Token Management**: JWT tokens expire after 8 hours (admin) / 30 minutes (user)
2. **Password Security**: All passwords are hashed using secure algorithms
3. **Principle of Least Privilege**: Users only get minimum required permissions
4. **Audit Logging**: All operations are logged with user context
5. **Separation of Concerns**: Admin and user systems are completely isolated
6. **Input Validation**: All API inputs are validated using Pydantic schemas

---

## Testing the Authorization System

### Test Scenarios:

#### 1. Admin Full Access:
- Login as admin → Should access all admin endpoints
- Use admin token on user endpoints → Should have full access (bypass all role restrictions)
- Try user endpoints with admin token → Should succeed even for Manager-only operations

#### 2. Admin Cross-Access Validation:
- Login as admin → Get admin JWT token  
- Use admin token to create projects → Should succeed (bypass Tester/Manager requirement)
- Use admin token to delete resources → Should succeed (bypass Manager-only requirement)
- Use admin token to view all user data → Should succeed (bypass role restrictions)

#### 3. Manager Permissions:
- Login as manager → Should have full CRUD on all user resources
- Try admin endpoints with user token → Should fail (insufficient permissions)

#### 4. Tester Limitations:
- Login as tester → Should create/read/update but NOT delete
- Try delete operations → Should return 403 Forbidden
- Try admin endpoints → Should fail (token type mismatch)

#### 5. Viewer Restrictions:
- Login as viewer → Should only read resources
- Try any create/update/delete → Should return 403 Forbidden

### Swagger UI Testing:

#### 🚀 **Enhanced Cross-Token Testing Experience:**

1. **Navigate to Swagger UI**: Go to `http://127.0.0.1:8000/docs`

2. **Option 1: Admin Cross-Access Testing (Full System Access)**:
   - Click the "Authorize" button (🔒) at the top of Swagger UI
   - You'll see **two authentication options**:
     - `AdminOAuth2PasswordBearer` - Admin authentication with cross-access
     - `UserOAuth2PasswordBearer` - Standard user authentication
   - Select `AdminOAuth2PasswordBearer`
   - Enter admin credentials: `admin@example.com` / `admin123`
   - Click "Authorize"
   - **Result**: 🎯 **Admin token works on ALL user API endpoints with unlimited access**

3. **Option 2: User Role-Based Testing**:
   - Click "Authorize" and select `UserOAuth2PasswordBearer`
   - Enter user credentials (manager@example.com/manager123, tester@example.com/tester123, or viewer@example.com/viewer123)
   - Click "Authorize"
   - **Result**: User token follows role-based restrictions

4. **Cross-Token Validation in Swagger**:
   ```
   ✅ Admin token on user endpoints → Full access (bypasses all role checks)
   ✅ Manager token → Full CRUD operations
   ✅ Tester token → CREATE, READ, UPDATE (no DELETE)  
   ✅ Viewer token → READ only
   ✅ Invalid tokens → 401 Unauthorized
   ✅ Insufficient permissions → 403 Forbidden
   ```

5. **Real-Time Testing Examples**:
   - **Admin Cross-Access**: Use admin auth to test `DELETE /api/v1/projects/{id}` → Should succeed (admin bypasses Manager-only restriction)
   - **Tester Limitation**: Use tester auth to test `DELETE /api/v1/projects/{id}` → Should return 403 Forbidden
   - **Viewer Restriction**: Use viewer auth to test `POST /api/v1/projects/` → Should return 403 Forbidden

#### 📋 **Swagger Testing Checklist**:
- [ ] Admin login works on both admin and user API sections  
- [ ] User login respects role-based permissions
- [ ] Cross-token authentication displays correctly in Swagger UI
- [ ] Error messages are clear and informative
- [ ] Token persistence works across different endpoint tests

### Token Type Validation:
```bash
# Verify admin token works on user APIs
curl -X GET "/api/v1/projects/" \
  -H "Authorization: Bearer <admin_token>"
# Expected: ✅ Success (admin has full access)

# Verify user token respects role limitations  
curl -X DELETE "/api/v1/projects/{id}" \
  -H "Authorization: Bearer <viewer_token>"
# Expected: ❌ 403 Forbidden (viewers cannot delete)

# Verify admin token bypasses role restrictions
curl -X DELETE "/api/v1/projects/{id}" \
  -H "Authorization: Bearer <admin_token>"  
# Expected: ✅ Success (admin bypasses all restrictions)
```

This comprehensive authorization system provides secure, role-based access control while maintaining simplicity for administrative operations and flexibility for user permissions.
