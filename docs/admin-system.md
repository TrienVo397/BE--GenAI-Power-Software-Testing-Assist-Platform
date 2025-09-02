# Admin System Documentation

## Overview

The GenAI Power Software Testing Assist Platform features a **simple, unified admin system** where all authenticated administrators have full system access without role restrictions or hierarchies.

## Admin System Architecture

### Core Principles

1. **Universal Access**: All authenticated admins have identical, complete system privileges
2. **No Role Hierarchy**: There are no different types or levels of admin users
3. **Cross-System Compatibility**: Admin tokens work on both admin and user API endpoints
4. **Simple Authentication**: Straightforward username/password authentication without complexity

### Admin Model

```python
class Admin(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    admin_username: str = Field(unique=True, index=True)
    admin_email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # No roles, permissions, or hierarchy fields
    # All admins have full access by default
```

## Admin Capabilities

### Full System Access

Authenticated admins can perform **any operation** on the platform:

| System Area | Admin Capabilities |
|-------------|-------------------|
| **Admin Management** | Create, read, update, delete other admins |
| **User Management** | Create, read, update, delete any user account |
| **Project Management** | Create, read, update, delete any project |
| **Content Management** | Access, modify, delete any project content |
| **System Configuration** | Full access to all system settings |
| **Database Operations** | Direct access to all data models |
| **API Access** | Can use both admin and user API endpoints |

### Admin Permissions Matrix

| Operation | Admin Access | User Access |
|-----------|--------------|-------------|
| **Admin Operations** |
| Create/manage admins | ✅ Full | ❌ None |
| Access admin panel | ✅ Full | ❌ None |
| System configuration | ✅ Full | ❌ None |
| **User Management** |
| Create any user | ✅ Full | ❌ Self only |
| Modify any user | ✅ Full | ❌ Self only |
| Delete any user | ✅ Full | ❌ Self only |
| View all users | ✅ Full | ❌ Project members only |
| **Project Management** |
| Access any project | ✅ Full | ❌ Member projects only |
| Modify any project | ✅ Full | ❌ Manager role only |
| Delete any project | ✅ Full | ❌ Manager role only |
| Manage project members | ✅ Full | ❌ Manager role only |
| **Content Operations** |
| Access all content | ✅ Full | ❌ Project-scoped |
| Modify any content | ✅ Full | ❌ Role-based |
| Delete any content | ✅ Full | ❌ Role-based |

## Authentication & Authorization

### Admin Authentication Flow

```http
# Step 1: Admin Login
POST /api/v1/admin/login
Content-Type: application/x-www-form-urlencoded

admin_username=admin&password=admin123

# Response: Admin JWT token with full privileges
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_type": "admin"
}

# Step 2: Use token for any operation
GET /api/v1/admin/users/all
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# OR use admin token on user endpoints (bypasses all restrictions)
GET /api/v1/projects/{any_project_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Authorization Logic

```python
# Admin authorization is simple - no permission checking needed
@router.get("/api/v1/admin/users/all")
async def list_all_users(
    current_admin: Admin = Depends(get_current_admin),  # Only validates token
    db: Session = Depends(get_db)
):
    # No further permission checks required
    # Admin has full access by default
    return user_crud.get_all_users(db)

# Admin tokens also work on user endpoints with full bypass
@router.get("/api/v1/projects/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    current_user: Union[User, Admin] = Depends(get_current_user_or_admin)
):
    if isinstance(current_user, Admin):
        # Admin bypass - no project membership check needed
        pass
    else:
        # Regular user - enforce project membership
        if not current_user.is_project_member(project_id):
            raise HTTPException(403, "Not a project member")
```

## Default Admin Accounts

### Pre-configured Admins

The system comes with two default admin accounts:

```
Admin Account 1:
- Username: admin
- Email: admin@example.com
- Password: admin123
- Full Name: System Administrator
- Department: IT
- Access: Complete system access

Admin Account 2:
- Username: admin2  
- Email: admin2@example.com
- Password: admin123
- Full Name: Secondary Admin
- Department: IT
- Access: Complete system access
```

### First Admin Setup

If no admins exist in the system, the first admin can be created using:

```http
POST /api/v1/admin/register
Content-Type: application/json

{
  "admin_username": "superadmin",
  "admin_email": "admin@company.com",
  "password": "secure_password",
  "full_name": "System Administrator",
  "department": "IT"
}
```

**Note**: This endpoint is only available when no admins exist in the database.

## Admin API Endpoints

### Admin Authentication
```http
POST   /api/v1/admin/register       # Register first admin (one-time only)
POST   /api/v1/admin/login          # Admin login
GET    /api/v1/admin/logout         # Admin logout
POST   /api/v1/admin/refresh        # Refresh admin token
```

### Admin Profile Management
```http
GET    /api/v1/admin/whoami         # Get current admin info
GET    /api/v1/admin/profile        # Get detailed admin profile
PUT    /api/v1/admin/profile        # Update own admin profile
```

### Admin Management
```http
GET    /api/v1/admin/all            # List all administrators
POST   /api/v1/admin/create         # Create new admin
GET    /api/v1/admin/{admin_id}     # Get specific admin details
PUT    /api/v1/admin/{admin_id}     # Update admin details
DELETE /api/v1/admin/{admin_id}     # Delete admin account
```

### User Management (Admin)
```http
GET    /api/v1/admin/users/all      # List all users
POST   /api/v1/admin/users/create   # Create new user
GET    /api/v1/admin/users/{id}     # Get user details
PUT    /api/v1/admin/users/{id}     # Update user
DELETE /api/v1/admin/users/{id}     # Delete user
GET    /api/v1/admin/users/stats    # Get user statistics
```

### Project Management (Admin)
```http
GET    /api/v1/admin/projects/all   # List all projects
POST   /api/v1/admin/projects       # Create project
GET    /api/v1/admin/projects/{id}  # Get project details
PUT    /api/v1/admin/projects/{id}  # Update project
DELETE /api/v1/admin/projects/{id}  # Delete project
GET    /api/v1/admin/projects/stats # Get project statistics
```

### System Management (Admin)
```http
GET    /api/v1/admin/system/status  # System health status
GET    /api/v1/admin/system/logs    # System logs
POST   /api/v1/admin/system/backup  # Create system backup
POST   /api/v1/admin/system/restore # Restore from backup
```

## Cross-System Token Usage

### Admin Tokens on User Endpoints

Admin tokens provide **full bypass access** on user endpoints:

```bash
# Admin can access any project regardless of membership
curl -X GET "/api/v1/projects/{any_project_id}" \
  -H "Authorization: Bearer <admin_token>"
# Result: Success - bypasses membership check

# Admin can access any user's chat sessions
curl -X GET "/api/v1/chat/sessions" \
  -H "Authorization: Bearer <admin_token>"
# Result: Success - returns all chat sessions

# Admin can run coverage analysis on any project
curl -X POST "/api/v1/bot/coverage-test" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "{any_project_id}"}'
# Result: Success - bypasses membership check

# Admin can add members to any project
curl -X POST "/api/v1/projects/{any_project_id}/members" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "{user_id}", "role": "MANAGER"}'
# Result: Success - bypasses manager role check
```

## Admin Operations Examples

### User Management
```bash
# List all users in the system
curl -X GET "/api/v1/admin/users/all" \
  -H "Authorization: Bearer <admin_token>"

# Create a new user
curl -X POST "/api/v1/admin/users/create" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "userpass123",
    "full_name": "Test User"
  }'

# Update any user's details
curl -X PUT "/api/v1/admin/users/{user_id}" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "email": "newemail@example.com"
  }'

# Delete any user
curl -X DELETE "/api/v1/admin/users/{user_id}" \
  -H "Authorization: Bearer <admin_token>"
```

### Project Management
```bash
# List all projects in the system
curl -X GET "/api/v1/admin/projects/all" \
  -H "Authorization: Bearer <admin_token>"

# Create a project (admin becomes manager)
curl -X POST "/api/v1/admin/projects" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin Created Project",
    "note": "Project created by administrator"
  }'

# Access any project's content
curl -X GET "/api/v1/project-artifacts/project/{any_project_id}" \
  -H "Authorization: Bearer <admin_token>"

# Delete any project
curl -X DELETE "/api/v1/admin/projects/{project_id}" \
  -H "Authorization: Bearer <admin_token>"
```

### Admin Management
```bash
# Create new admin
curl -X POST "/api/v1/admin/create" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_username": "newadmin",
    "admin_email": "newadmin@example.com",
    "password": "adminpass123",
    "full_name": "New Administrator",
    "department": "Support"
  }'

# List all admins
curl -X GET "/api/v1/admin/all" \
  -H "Authorization: Bearer <admin_token>"

# Update admin profile
curl -X PUT "/api/v1/admin/{admin_id}" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Admin Name",
    "department": "Operations"
  }'
```

## Security Considerations

### Admin Security Model

1. **Credential-Based Access**: Simple username/password authentication
2. **Full Trust Model**: All admins are equally trusted with complete access
3. **No Permission Escalation**: Admins cannot escalate beyond full access (already have it)
4. **Session Management**: Admin sessions are managed through JWT tokens
5. **Cross-System Access**: Admin tokens work across both admin and user APIs

### Security Best Practices

1. **Strong Passwords**: Ensure all admin accounts use strong passwords
2. **Account Monitoring**: Monitor admin account access and activities
3. **Regular Updates**: Change default admin passwords in production
4. **Access Logging**: Log all admin operations for audit purposes
5. **Backup Access**: Maintain multiple admin accounts for system recovery

### Production Security Recommendations

```bash
# Change default admin passwords immediately
curl -X PUT "/api/v1/admin/profile" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "complex_production_password_2025!"
  }'

# Create additional admin accounts for redundancy
curl -X POST "/api/v1/admin/create" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_username": "backup_admin",
    "admin_email": "backup@company.com",
    "password": "another_secure_password",
    "full_name": "Backup Administrator"
  }'
```

## Troubleshooting

### Common Admin Issues

1. **Login Failures**:
   ```bash
   # Check if admin account exists and is active
   GET /api/v1/admin/all
   
   # Verify credentials are correct
   POST /api/v1/admin/login
   ```

2. **Token Expiration**:
   ```bash
   # Refresh expired admin token
   POST /api/v1/admin/refresh
   Authorization: Bearer <expired_admin_token>
   ```

3. **Access Denied on User Endpoints**:
   ```bash
   # Ensure using admin token, not user token
   # Admin tokens should bypass all user-level restrictions
   ```

4. **First Admin Creation**:
   ```bash
   # Only works when no admins exist in database
   POST /api/v1/admin/register
   # If fails, at least one admin already exists
   ```

### Debug Admin Access

```python
# Check if token is admin token
def debug_token_type(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_type = payload.get("type", "user")
    print(f"Token type: {user_type}")
    
    if user_type == "admin":
        print("✅ Admin token - has full system access")
    else:
        print("❌ User token - project-restricted access")

# Verify admin permissions
def debug_admin_access(admin_id: str, db: Session):
    admin = admin_crud.get_admin_by_id(db, admin_id)
    if admin and admin.is_active:
        print("✅ Admin has full access to all operations")
    else:
        print("❌ Admin account inactive or not found")
```

This simple admin system prioritizes ease of management while providing complete system control to authenticated administrators.
