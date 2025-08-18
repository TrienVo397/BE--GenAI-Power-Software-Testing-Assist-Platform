# Separated Admin System Documentation

## Overview

The platform now features a completely **separated admin system** with dedicated models, authentication, and permissions, isolated from regular user functionality for enhanced security.

## Architecture Design

### 🔐 **Separation of Concerns**
- **Regular Users**: Application users who work with projects, documents, and AI tools
- **Admin Users**: System administrators with elevated privileges for user and system management

### 🏗️ **Model Structure**

#### Admin Models (`app/models/admin.py`)
```python
class Admin(SQLModel, table=True):
    # Separate admin identity
    admin_username: str
    admin_email: str
    
    # Admin-specific roles
    admin_roles: str  # JSON: ["super_admin", "system_admin", "user_admin"]
    is_super_admin: bool
    requires_2fa: bool
    
    # Security audit fields
    created_by: Optional[uuid.UUID]  # Which admin created this admin
    linked_user_id: Optional[uuid.UUID]  # Optional link to regular user
```

#### Admin Credentials (`app/models/admin_credential.py`)
```python
class AdminCredential(SQLModel, table=True):
    # Enhanced security for admin authentication
    admin_id: uuid.UUID
    hashed_password: str
    
    # 2FA requirements
    requires_2fa: bool = True
    totp_secret: Optional[str]
    backup_codes: Optional[str]
    
    # Security lockout mechanisms
    failed_login_attempts: int
    locked_until: Optional[datetime]
    password_expires_at: Optional[datetime]
```

#### Regular User Model (`app/models/user.py`)
```python
class User(SQLModel, table=True):
    # Simplified user roles (removed admin)
    roles: str  # JSON: ["manager", "tester", "viewer"]
    
    # Application-focused functionality
    # No admin capabilities
```

## 🔑 **Role Hierarchy**

### Admin Roles (System Level)
1. **Super Admin** (`super_admin`)
   - Can manage other admins
   - Full system control
   - Cannot be self-demoted if last super admin

2. **System Admin** (`system_admin`)
   - User management
   - System configuration
   - Cannot manage other admins

3. **User Admin** (`user_admin`)
   - User management only
   - Limited system access

### User Roles (Application Level)
1. **Manager** (`manager`)
   - Project management
   - AI tool access
   - Document management

2. **Tester** (`tester`)
   - Testing operations
   - AI RTM generation
   - Limited project management

3. **Viewer** (`viewer`)
   - Read-only access

## 🛡️ **Security Features**

### Admin Security
- **Mandatory 2FA**: All admins require two-factor authentication
- **Password Expiration**: 90-day password rotation
- **Account Lockout**: 5 failed attempts = 30-minute lockout
- **Audit Trail**: All admin actions logged with creator tracking
- **Self-Protection**: Cannot delete self or demote last super admin

### User Security
- **Role-Based Permissions**: Fine-grained access control
- **Session Management**: Separate from admin sessions
- **Limited Escalation**: Users cannot become admins through application

## 📍 **API Endpoints**

### Admin Endpoints (`/api/v1/admin/`)
```
Authentication:
POST /admin/register        # First super admin only
POST /admin/login          # Admin authentication

Admin Management:
GET  /admin/profile        # Current admin profile
GET  /admin/all           # List all admins (super admin)
POST /admin/create        # Create new admin (super admin)
PUT  /admin/{id}          # Update admin (super admin)
PUT  /admin/{id}/roles    # Update admin roles (super admin)

User Management via Admin:
GET  /admin/users/all     # List all users (user admin+)
POST /admin/users/create  # Create user (user admin+)
PUT  /admin/users/{id}    # Update user (user admin+)
DEL  /admin/users/{id}    # Delete user (user admin+)
```

### Regular User Endpoints (`/api/v1/users/`)
```
Authentication:
POST /users/register      # Public registration
POST /users/login        # User authentication
POST /users/token        # Token-based login

Self-Service:
GET  /users/me           # Own profile
PUT  /users/me/profile   # Update own profile

Limited User Operations:
GET  /users/all          # List users (with permissions)
GET  /users/{id}         # Get user (self or with permissions)
```

## 🚀 **Initial Setup Process**

### 1. Create First Super Admin
```bash
POST /api/v1/admin/register
{
  "admin_username": "superadmin",
  "admin_email": "admin@company.com",
  "password": "secure_password",
  "full_name": "System Administrator",
  "department": "IT"
}
```

### 2. Admin Login
```bash
POST /api/v1/admin/login
{
  "admin_username": "superadmin",
  "password": "secure_password",
  "totp_code": "123456"  # If 2FA enabled
}
```

### 3. Create Additional Admins
```bash
POST /api/v1/admin/create
{
  "admin_username": "useradmin",
  "admin_email": "useradmin@company.com",
  "admin_roles": ["user_admin"],
  "department": "Support"
}
```

### 4. Create Regular Users
```bash
POST /api/v1/admin/users/create
{
  "username": "tester1",
  "email": "tester1@company.com",
  "password": "user_password",
  "initial_roles": ["tester"]
}
```

## 🔧 **Implementation Benefits**

### ✅ **Enhanced Security**
- Complete separation of admin and user authentication
- No privilege escalation paths from user to admin
- Dedicated security controls for each user type

### ✅ **Clear Responsibility**
- Admins manage the system and users
- Users work with application features
- No role confusion or overlap

### ✅ **Audit & Compliance**
- Full admin action logging
- Clear accountability chains
- Separate credential management

### ✅ **Scalability**
- Independent scaling of admin vs user features
- Separate database tables and indexes
- Focused permission systems

## 🔄 **Migration from Previous System**

### Database Changes
1. **New Tables**: `admin`, `admin_credential`
2. **Updated User Table**: Remove admin role, simplify permissions
3. **Data Migration**: Convert existing admin users to separate admin records

### Code Changes
1. **Separate Auth Systems**: `admin_auth.py` vs `auth.py`
2. **Permission Systems**: Admin permissions vs user permissions
3. **API Endpoints**: Dedicated admin routes

### Deployment Steps
1. Run database migration to create admin tables
2. Create first super admin account
3. Migrate existing admin users to admin system
4. Update client applications to use separate admin interface
5. Remove admin roles from regular user system

This separated admin system provides **enterprise-grade security** with clear separation between system administration and application usage! 🎉
