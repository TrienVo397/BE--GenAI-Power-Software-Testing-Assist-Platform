# Project Member Management API

## Overview

This document describes the API endpoints for managing project memberships in the project-based authorization system. All endpoints require user authentication and appropriate project permissions.

## Authentication

All endpoints require a valid JWT token in the Authorization header:
```http
Authorization: Bearer <jwt_token>
```

## Base URL

All endpoints are prefixed with `/api/v1`

## Endpoints

### Get Available Project Roles

Get information about available project roles and their permissions.

```http
GET /project-roles
```

**Response:**
```json
{
  "roles": [
    {
      "role": "MANAGER",
      "can_manage_project": true,
      "can_manage_members": true,
      "can_modify_content": true,
      "can_create_artifacts": true,
      "is_read_only": false
    },
    {
      "role": "TESTER",
      "can_manage_project": false,
      "can_manage_members": false,
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

### Get Project Members

Get all members of a specific project.

```http
GET /projects/{project_id}/members
```

**Requirements:**
- User must be a member of the project

**Query Parameters:**
- `active_only` (boolean, optional): Filter active members only (default: true)

**Response:**
```json
{
  "project_id": "3e99fa3e-4afa-47d3-a6c1-cf1c1ebeca71",
  "project_name": "Sample Testing Project",
  "total_members": 2,
  "members": [
    {
      "project_id": "3e99fa3e-4afa-47d3-a6c1-cf1c1ebeca71",
      "user_id": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
      "role": "MANAGER",
      "is_active": true,
      "joined_at": "2025-01-15T10:30:00Z",
      "added_by": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
      "updated_at": "2025-01-15T10:30:00Z",
      "user_username": "user1",
      "user_email": "user1@example.com",
      "user_full_name": "User One"
    }
  ]
}
```

### Add Project Member

Add a user to a project with a specific role.

```http
POST /projects/{project_id}/members
```

**Requirements:**
- User must have MANAGER role in the project

**Request Body:**
```json
{
  "user_id": "db92abca-18fd-484f-baed-bde2358343a3",
  "role": "TESTER",
  "is_active": true
}
```

**Response:**
```json
{
  "project_id": "3e99fa3e-4afa-47d3-a6c1-cf1c1ebeca71",
  "user_id": "db92abca-18fd-484f-baed-bde2358343a3",
  "role": "TESTER",
  "is_active": true,
  "joined_at": "2025-01-15T14:30:00Z",
  "added_by": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
  "updated_at": "2025-01-15T14:30:00Z",
  "user_username": "user2",
  "user_email": "user2@example.com",
  "user_full_name": "User Two"
}
```

### Update Member Role

Update a user's role in a project.

```http
PUT /projects/{project_id}/members/{user_id}
```

**Requirements:**
- User must have MANAGER role in the project
- Cannot demote the last MANAGER

**Request Body:**
```json
{
  "role": "VIEWER",
  "is_active": true
}
```

**Response:**
```json
{
  "project_id": "3e99fa3e-4afa-47d3-a6c1-cf1c1ebeca71",
  "user_id": "db92abca-18fd-484f-baed-bde2358343a3",
  "role": "VIEWER",
  "is_active": true,
  "joined_at": "2025-01-15T14:30:00Z",
  "added_by": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
  "updated_at": "2025-01-15T15:45:00Z",
  "updated_by": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
  "user_username": "user2",
  "user_email": "user2@example.com",
  "user_full_name": "User Two"
}
```

### Remove Project Member

Remove a user from a project.

```http
DELETE /projects/{project_id}/members/{user_id}
```

**Requirements:**
- User must have MANAGER role in the project
- Cannot remove the last MANAGER
- Cannot remove self if last MANAGER

**Response:**
```json
{
  "message": "User removed from project successfully",
  "removed_member": {
    "user_id": "db92abca-18fd-484f-baed-bde2358343a3",
    "user_username": "user2",
    "role": "VIEWER"
  }
}
```

### Get User's Project Memberships

Get all projects a user is a member of.

```http
GET /users/{user_id}/projects
```

**Requirements:**
- Can only view own memberships unless admin
- Admins can view any user's memberships

**Response:**
```json
{
  "user_id": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
  "user_username": "user1",
  "total_projects": 2,
  "memberships": [
    {
      "project_id": "3e99fa3e-4afa-47d3-a6c1-cf1c1ebeca71",
      "user_id": "d6e168ab-ace6-4d52-980b-ab5a87ff0f44",
      "role": "MANAGER",
      "is_active": true,
      "joined_at": "2025-01-15T10:30:00Z",
      "project_name": "Sample Testing Project"
    }
  ]
}
```

### Bulk Add Members

Add multiple users to a project at once.

```http
POST /projects/{project_id}/members/bulk
```

**Requirements:**
- User must have MANAGER role in the project

**Request Body:**
```json
{
  "user_roles": [
    {
      "user_id": "db92abca-18fd-484f-baed-bde2358343a3",
      "role": "TESTER",
      "is_active": true
    },
    {
      "user_id": "e0204c83-d885-49a2-925b-4adf9c13f477",
      "role": "VIEWER",
      "is_active": true
    }
  ]
}
```

**Response:**
```json
{
  "message": "Successfully added 2 members to project",
  "added_members": [
    {
      "user_id": "db92abca-18fd-484f-baed-bde2358343a3",
      "role": "TESTER",
      "user_username": "user2"
    },
    {
      "user_id": "e0204c83-d885-49a2-925b-4adf9c13f477",
      "role": "VIEWER",
      "user_username": "user3"
    }
  ],
  "failed_members": []
}
```

## Error Responses

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Project or user not found |
| 409 | Conflict - User already a member |

### Error Response Format

```json
{
  "detail": "Access denied: Only project managers can manage members"
}
```

### Specific Error Scenarios

#### 403 - Not Project Member
```json
{
  "detail": "Access denied: Not a project member"
}
```

#### 403 - Insufficient Role
```json
{
  "detail": "Access denied: Manager role required for this operation"
}
```

#### 404 - Project Not Found
```json
{
  "detail": "Project not found or access denied"
}
```

#### 409 - Already Member
```json
{
  "detail": "User is already a member of this project"
}
```

#### 400 - Cannot Remove Last Manager
```json
{
  "detail": "Cannot remove the last manager from the project"
}
```

## Usage Examples

### Python Example

```python
import requests

base_url = "http://localhost:8000/api/v1"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

# Get project members
response = requests.get(
    f"{base_url}/projects/{project_id}/members",
    headers=headers
)
members = response.json()

# Add a member
new_member = {
    "user_id": "user-uuid-here",
    "role": "TESTER",
    "is_active": True
}
response = requests.post(
    f"{base_url}/projects/{project_id}/members",
    headers=headers,
    json=new_member
)

# Update member role
updated_role = {"role": "VIEWER"}
response = requests.put(
    f"{base_url}/projects/{project_id}/members/{user_id}",
    headers=headers,
    json=updated_role
)
```

### JavaScript Example

```javascript
const baseUrl = 'http://localhost:8000/api/v1';
const headers = {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
};

// Get project members
const members = await fetch(`${baseUrl}/projects/${projectId}/members`, {
    headers
}).then(r => r.json());

// Add member
const newMember = {
    user_id: 'user-uuid-here',
    role: 'TESTER',
    is_active: true
};

await fetch(`${baseUrl}/projects/${projectId}/members`, {
    method: 'POST',
    headers,
    body: JSON.stringify(newMember)
});
```

### cURL Examples

```bash
# Get project members
curl -X GET \
  "http://localhost:8000/api/v1/projects/{project_id}/members" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Add member
curl -X POST \
  "http://localhost:8000/api/v1/projects/{project_id}/members" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid-here",
    "role": "TESTER",
    "is_active": true
  }'

# Update member role
curl -X PUT \
  "http://localhost:8000/api/v1/projects/{project_id}/members/{user_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "VIEWER"}'

# Remove member
curl -X DELETE \
  "http://localhost:8000/api/v1/projects/{project_id}/members/{user_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Business Rules

### Role Assignment Rules

1. **MANAGER**:
   - Full control over project and members
   - Can assign any role to any user
   - Cannot remove self if last manager
   - Project creator automatically becomes MANAGER

2. **TESTER**:
   - Can create and modify project content
   - Cannot manage project members
   - Cannot delete other users' artifacts

3. **VIEWER**:
   - Read-only access to all project content
   - Cannot modify any project data
   - Can participate in AI chat sessions

### Membership Rules

1. **Project Creation**: Creator automatically becomes MANAGER
2. **Last Manager Protection**: Cannot remove the last MANAGER
3. **Self-Management**: Users can leave projects unless they're the last MANAGER
4. **Active Status**: Memberships can be deactivated temporarily
5. **Audit Trail**: All membership changes are logged

## Rate Limiting

Member management endpoints are rate-limited to prevent abuse:

- **GET endpoints**: 100 requests per minute
- **POST/PUT/DELETE endpoints**: 20 requests per minute

## Pagination

Endpoints returning multiple members support pagination:

- `skip` (default: 0): Number of records to skip
- `limit` (default: 100, max: 1000): Number of records to return

```http
GET /projects/{project_id}/members?skip=0&limit=50
```
