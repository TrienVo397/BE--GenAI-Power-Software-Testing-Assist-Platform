# Project Membership System

## Overview

The Project Membership system allows you to assign users to projects with specific roles, providing fine-grained access control at the project level. This complements the existing global user roles (MANAGER, TESTER, VIEWER) with project-specific roles.

## Project Roles

Each user can have different roles in different projects:

### Available Roles

- **OWNER**: Full control over the project, can manage members and project settings
- **LEAD**: Project lead, can manage project settings and members  
- **MANAGER**: Can manage project content and moderate discussions
- **DEVELOPER**: Can contribute to project development and testing
- **TESTER**: Can create and manage test artifacts
- **REVIEWER**: Can review and comment on project content
- **VIEWER**: Read-only access to project content

### Role Permissions

| Action | OWNER | LEAD | MANAGER | DEVELOPER | TESTER | REVIEWER | VIEWER |
|--------|-------|------|---------|-----------|--------|----------|---------|
| Manage Project Settings | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Add/Remove Members | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Modify Content | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Create Artifacts | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Read-only Access | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

## API Endpoints

### Add Member to Project
```http
POST /api/v1/projects/{project_id}/members
Content-Type: application/json

{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "DEVELOPER",
  "is_active": true
}
```

### Get Project Members
```http
GET /api/v1/projects/{project_id}/members?active_only=true
```

Response:
```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "project_name": "My Project",
  "total_members": 3,
  "members": [
    {
      "project_id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "123e4567-e89b-12d3-a456-426614174001",
      "role": "OWNER",
      "is_active": true,
      "joined_at": "2025-08-25T10:00:00Z",
      "user_username": "alice",
      "user_email": "alice@example.com",
      "user_full_name": "Alice Johnson",
      "project_name": "My Project"
    }
  ]
}
```

### Get User's Project Memberships
```http
GET /api/v1/users/{user_id}/projects?active_only=true
```

### Update Member Role
```http
PUT /api/v1/projects/{project_id}/members/{user_id}
Content-Type: application/json

{
  "role": "LEAD",
  "is_active": true
}
```

### Remove Member from Project
```http
DELETE /api/v1/projects/{project_id}/members/{user_id}
```

### Add Multiple Members
```http
POST /api/v1/projects/{project_id}/members/batch
Content-Type: application/json

{
  "user_roles": [
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174001",
      "role": "DEVELOPER"
    },
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174002", 
      "role": "TESTER"
    }
  ]
}
```

### Get Available Project Roles
```http
GET /api/v1/project-roles
```

Response:
```json
{
  "roles": [
    {
      "role": "OWNER",
      "can_manage_project": true,
      "can_manage_members": true,
      "can_modify_content": true,
      "can_create_artifacts": true,
      "is_read_only": false
    },
    {
      "role": "VIEWER",
      "can_manage_project": false,
      "can_manage_members": false,
      "can_modify_content": false,
      "can_create_artifacts": false,
      "is_read_only": true
    }
  ]
}
```

## Usage Examples

### Example 1: Create a Project and Add Team Members

```python
# 1. Create a project (requires global MANAGER/TESTER role or admin)
project_data = {
    "name": "Web Application Testing",
    "note": "Testing project for our web app",
    "meta_data": "{\"type\": \"web_testing\"}"
}

# 2. Add team members with different roles
members = [
    {"user_id": "alice-uuid", "role": "OWNER"},      # Project owner
    {"user_id": "bob-uuid", "role": "LEAD"},         # Technical lead
    {"user_id": "charlie-uuid", "role": "DEVELOPER"}, # Developer
    {"user_id": "diana-uuid", "role": "TESTER"},     # QA tester
    {"user_id": "eve-uuid", "role": "REVIEWER"},     # Code reviewer
    {"user_id": "frank-uuid", "role": "VIEWER"}      # Stakeholder
]

# Add members in batch
POST /api/v1/projects/{project_id}/members/batch
{
  "user_roles": members
}
```

### Example 2: Project Role Hierarchy

```python
# A user can have different roles in different projects:

# Alice's memberships:
# - Project A: OWNER (can manage everything)
# - Project B: DEVELOPER (can code and create artifacts)  
# - Project C: VIEWER (read-only access)

# Bob's memberships:
# - Project A: LEAD (can manage project and members)
# - Project B: OWNER (full control)
# - Project D: TESTER (testing focused)
```

### Example 3: Permission Checking

```python
# Check if user can manage a specific project
user = get_current_user()
project_id = "123e4567-e89b-12d3-a456-426614174000"

# Option 1: Check global permissions
can_manage_globally = user.can_manage_projects()  # Based on global role

# Option 2: Check project-specific permissions  
can_manage_project = user.can_manage_project_members(project_id)  # Based on project role

# Option 3: Check via CRUD
can_manage = project_member_crud.user_can_manage_members(db, project_id, user.id)
```

## Database Schema

### ProjectMember Table

```sql
CREATE TABLE projectmember (
    project_id UUID REFERENCES project(id),
    user_id UUID REFERENCES user(id),
    role VARCHAR NOT NULL,  -- ProjectRole enum
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT NOW(),
    added_by UUID REFERENCES user(id),
    updated_at TIMESTAMP DEFAULT NOW(), 
    updated_by UUID REFERENCES user(id),
    PRIMARY KEY (project_id, user_id)
);
```

## Integration with Existing System

### Global vs Project Roles

The system now supports two levels of role-based access:

1. **Global User Roles** (existing): MANAGER, TESTER, VIEWER
   - Control general system access
   - Required for creating projects, accessing admin functions
   
2. **Project Roles** (new): OWNER, LEAD, MANAGER, DEVELOPER, TESTER, REVIEWER, VIEWER  
   - Control access within specific projects
   - Allow fine-grained project-level permissions

### Permission Resolution

When checking permissions for project-related actions:

1. **Admin users**: Always have full access (via cross-token support)
2. **Global permissions**: Users with global MANAGER role can manage any project
3. **Project permissions**: Users with appropriate project role can manage that specific project
4. **Combined check**: `global_permission OR project_permission`

Example:
```python
# A user can manage project members if they:
# 1. Have global MANAGER role (can manage any project), OR  
# 2. Have OWNER/LEAD role in that specific project

can_manage = (
    current_user.can_manage_projects() OR  # Global permission
    project_member_crud.user_can_manage_members(db, project_id, current_user.id)  # Project permission
)
```

This provides flexibility where:
- Global managers can oversee all projects
- Project owners/leads can manage their specific projects
- Regular users can have different responsibilities in different projects
