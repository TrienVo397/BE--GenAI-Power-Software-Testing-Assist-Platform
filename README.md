# GenAI-Powered Software Testing Assistance Platform - Backend

A modern, production-ready FastAPI backend for a GenAI-powered software testing assistance platform. Built with SQLModel, featuring comprehensive role-based authorization, admin cross-access capabilities, and AI agent integration for intelligent testing workflows.

## 🎯 Platform Overview

This platform provides AI-powered testing assistance through conversational interfaces, where testers can:
- Upload documents to project knowledge bases
- Use conversational commands for test planning operations  
- Interact with AI agents through chat interfaces for testing guidance
- Generate and manage test artifacts through conversational AI

## ✨ Key Features

- **FastAPI**: High-performance web framework with automatic API documentation
- **SQLModel**: Modern SQL databases with Python, designed by the creator of FastAPI
- **Dual Authentication System**: Separate admin and user authentication with cross-access support
- **Role-Based Authorization**: Granular permissions with Manager, Tester, and Viewer roles
- **Admin Cross-Access**: Admins can access all user APIs with full privileges
- **Swagger UI Cross-Token Support**: Enhanced Swagger interface supporting both authentication types
- **AI Agent Integration**: LangGraph-based conversation agents for testing assistance
- **Project-Centric Workflow**: Organized around testing projects and document versions
- **Chat-Based Interaction**: Conversational AI interface for natural testing guidance
- **Comprehensive Testing Suite**: Full pytest setup with test coverage

## 🏗️ Architecture & Project Structure

```
BE--GenAI-Power-Software-Testing-Assist-Platform/
├── app/                     # Main application package
│   ├── main.py             # Application entry point with custom OpenAPI schema
│   ├── api/                # API layer with versioned endpoints
│   │   ├── deps.py        # Dependency injection and shared dependencies
│   │   └── v1/            # API version 1
│   │       ├── api.py      # Main API router configuration
│   │       └── endpoints/  # Individual endpoint handlers
│   │           ├── chat.py                 # Chat session and messaging
│   │           ├── document_versions.py    # Document version management
│   │           ├── files.py               # File upload and management
│   │           ├── projects.py            # Project CRUD operations
│   │           ├── project_artifacts.py   # Artifact management
│   │           └── users.py               # User management
│   ├── core/               # Core application configuration
│   │   ├── config.py      # Application settings and environment
│   │   ├── database.py    # Database connection and session management
│   │   ├── security.py    # JWT authentication and password hashing
│   │   ├── permissions.py # Permission definitions and role validation
│   │   └── authz.py       # Authorization system with cross-token support
│   ├── crud/              # CRUD operations for database entities
│   │   ├── base.py        # Base CRUD class with common operations
│   │   ├── chat_crud.py   # Chat session and message operations
│   │   ├── credential_crud.py      # User credential management
│   │   ├── document_version_crud.py # Document version operations
│   │   ├── project_artifact_crud.py # Artifact management operations
│   │   ├── project_crud.py         # Project management operations
│   │   └── user_crud.py           # User management operations
│   ├── models/            # SQLModel database models
│   │   ├── chat.py        # ChatSession and ChatMessage models
│   │   ├── credential.py  # User credential model
│   │   ├── document_version.py # Document versioning model
│   │   ├── project_artifact.py # Project artifact model
│   │   ├── project.py     # Core project model
│   │   └── user.py        # User model with role management
│   ├── schemas/           # Pydantic schemas for API validation
│   │   ├── chat.py        # Chat-related request/response schemas
│   │   ├── document_version.py # Document version schemas
│   │   ├── file.py        # File operation schemas
│   │   ├── project_artifact.py # Artifact schemas
│   │   ├── project.py     # Project schemas
│   │   └── user.py        # User schemas with role validation
│   └── utils/             # Utility functions and helpers
│       └── project_fs.py  # File system operations for projects
├── ai/                    # AI agent implementation
│   └── agents/            # Production AI agent modules
│       └── conversation_agent.py # LangGraph-based conversational AI
├── data/                  # Project data storage (Git-tracked)
│   ├── default/           # Default project resources
│   │   ├── prompts/       # Default system prompts
│   │   └── templates/     # Default project templates
│   └── project-{uuid}/    # Individual project workspaces
│       ├── artifacts/     # Generated test artifacts
│       ├── templates/     # Project-specific templates
│       └── versions/      # Document version history
├── docs/                  # Comprehensive documentation
│   ├── authorization-system.md # Complete authorization documentation
│   ├── chat-api-documentation.md # Chat API reference
│   └── file_editing_api.md     # File management API reference
├── scripts/               # Database management scripts
│   └── seed_data.py      # Database seeding with test accounts
├── tests/                 # Comprehensive test suite
└── manage.py             # Database management commands
```

### 🔑 Key Relationships & Data Flow

- **User** → **Project** (one-to-many) - Users own and manage projects
- **Project** → **ProjectArtifact** (one-to-many) - Projects contain test artifacts
- **Project** → **DocumentVersion** (one-to-many) - Projects track document versions
- **Project** → **ChatSession** (one-to-many) - AI conversations are project-scoped
- **ChatSession** → **ChatMessage** (one-to-many) - Conversation message history
- **User** → **Credential** (one-to-one) - Secure credential storage

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd BE--GenAI-Power-Software-Testing-Assist-Platform
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows PowerShell
   python -m venv venv
   venv\Scripts\Activate.ps1
   
   # Windows Command Prompt  
   python -m venv venv
   venv\Scripts\activate.bat
   
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database and seed test data:**
   ```bash
   # Reset database and create initial admin/user accounts
   python manage.py reset-db
   
   # This will:
   # - Drop existing database tables
   # - Create fresh database schema  
   # - Seed with default admin and user accounts
   ```

5. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The API will be available at `http://127.0.0.1:8000`

## 📚 API Documentation & Testing

Once the server is running, access the comprehensive API documentation:

- **🎯 Interactive Swagger UI**: http://127.0.0.1:8000/docs
  - Features **dual authentication** options (Admin + User OAuth2)
  - **Cross-token support** - Admin tokens work on user endpoints
  - Real-time API testing with full authentication flow
  - Automatic parameter detection and validation

- **📖 Alternative Documentation (ReDoc)**: http://127.0.0.1:8000/redoc
  - Clean, readable API reference
  - Detailed schema documentation

- **⚡ OpenAPI Schema**: http://127.0.0.1:8000/openapi.json
  - Raw OpenAPI 3.0 specification for API integration

## 🔐 Authentication & Authorization System

This platform features a **sophisticated dual-tier authorization system** with admin cross-access capabilities and comprehensive role-based permissions.

### 🎯 Test Accounts (Auto-Created)

After running `python manage.py reset-db`, these accounts are available:

#### 👨‍💼 **Admin Accounts** (System Administration)
```
Admin Login: POST /api/v1/admin/login

📧 admin@example.com  
🔐 admin123
🎭 Full system access + cross-access to all user APIs
```

#### 👥 **User Accounts** (Application Usage)
```  
User Login: POST /api/v1/users/login

📧 manager@example.com  🔐 manager123  🎭 MANAGER (Full CRUD operations)
📧 tester@example.com   🔐 tester123   🎭 TESTER (CREATE, READ, UPDATE)  
📧 viewer@example.com   🔐 viewer123   🎭 VIEWER (READ only)
```

### 🚀 **Cross-Token Authentication in Swagger UI**

The Swagger UI at `/docs` supports **dual authentication** with cross-token capabilities:

1. **🔑 Admin Cross-Access** (Recommended for testing):
   - Click "Authorize" → Select `AdminOAuth2PasswordBearer`
   - Login: `admin@example.com` / `admin123`
   - **Result**: Admin token works on **ALL** user API endpoints with full privileges

2. **👤 User Role-Based Access**:
   - Click "Authorize" → Select `UserOAuth2PasswordBearer`  
   - Login with any user account
   - **Result**: Token follows role-based permission restrictions

### 📋 **Permission Matrix**

| Feature | Admin | Manager | Tester | Viewer |
|---------|-------|---------|--------|--------|
| **User Management** | ✅ Full | ✅ Limited | ❌ | ❌ |
| **Projects** | ✅ Full | ✅ Full | ✅ CRU | ✅ Read |
| **Documents** | ✅ Full | ✅ Full | ✅ CRU | ✅ Read |
| **Artifacts** | ✅ Full | ✅ Full | ✅ CRU | ✅ Read |
| **Files** | ✅ Full | ✅ Full | ✅ CRU | ✅ Read |
| **Chat/AI** | ✅ Full | ✅ Full | ✅ CRU | ✅ Read |

*Legend: Full = All operations, CRU = Create/Read/Update (no Delete)*

### 🛡️ **Key Security Features**

- **🔐 Separated Authentication**: Admin and user systems completely isolated
- **🎯 Admin Cross-Access**: Admins can use admin tokens on user endpoints  
- **🚫 No Public Registration**: Only admins can create users
- **🎭 Role-Based Permissions**: Granular access control for users
- **🔄 Cross-Token Swagger**: Seamless testing with both authentication types
- **🔒 JWT Security**: Secure token-based authentication with expiration

## 🔌 API Endpoints Reference

### 🔐 **Admin System** (`/api/v1/admin/*`)

#### Authentication & Profile
```
POST   /admin/register       # Register first admin (when no admins exist)
POST   /admin/login          # Admin login (OAuth2) → Returns admin JWT
GET    /admin/whoami         # Current admin quick info
GET    /admin/profile        # Current admin detailed profile  
```

#### Admin Management (Admin Only)
```
GET    /admin/all            # List all admins
POST   /admin/create         # Create new admin
PUT    /admin/{admin_id}     # Update admin
DELETE /admin/{admin_id}     # Delete admin
```

#### Cross-Access User Management (Admin Only)
```
GET    /admin/users/all      # List all users
POST   /admin/users/create   # Create new user  
PUT    /admin/users/{id}     # Update any user
DELETE /admin/users/{id}     # Delete any user
PUT    /admin/users/{id}/roles # Update user roles
```

### 👥 **User System** (`/api/v1/users/*`)

#### Authentication & Self-Service
```
POST   /users/register       # DISABLED (admin-only user creation)
POST   /users/login          # User login (OAuth2) → Returns user JWT  
GET    /users/whoami         # Current user quick info
GET    /users/me             # Current user profile
PUT    /users/me/profile     # Update own profile
```

#### User Operations (Permission-Based)
```
GET    /users/all            # List users (USER_READ permission)
GET    /users/{user_id}      # Get user (self or USER_READ permission)
```

### 🎯 **Core Application APIs**

#### Project Management
```
POST   /projects/            # Create project (Manager/Tester)
GET    /projects/            # List projects (All authenticated users)
GET    /projects/{id}        # Get project details (All)
PUT    /projects/{id}        # Update project (Manager/Tester)  
DELETE /projects/{id}        # Delete project (Manager only)
```

#### Document Version Management
```
POST   /document-versions/   # Create version (Manager/Tester)
GET    /document-versions/project/{id} # Get project versions (All)
GET    /document-versions/project/{id}/current # Get current version (All)
PUT    /document-versions/{id} # Update version (Manager/Tester)
DELETE /document-versions/{id} # Delete version (Manager only)
```

#### Test Artifact Management  
```
POST   /project-artifacts/   # Create artifact (Manager/Tester)
GET    /project-artifacts/   # List artifacts (All)
GET    /project-artifacts/project/{id} # Get project artifacts (All)  
PUT    /project-artifacts/{id} # Update artifact (Manager/Tester)
DELETE /project-artifacts/{id} # Delete artifact (Manager only)
```

#### File Management
```
GET    /projects/{id}/files  # List project files (All)
GET    /projects/{id}/files/{path} # Get file (All)
POST   /projects/{id}/files/{path} # Upload file (Manager/Tester)
PUT    /projects/{id}/files/{path} # Update file (Manager/Tester)
DELETE /projects/{id}/files/{path} # Delete file (Manager only)
```

#### AI-Powered Chat System
```
POST   /chat/sessions        # Create chat session (Manager/Tester)
GET    /chat/sessions        # List chat sessions (All)
GET    /chat/sessions/{id}   # Get chat session (All)
GET    /chat/sessions/{id}/messages # Get session messages (All)
PUT    /chat/sessions/{id}   # Update session (Manager/Tester)
DELETE /chat/sessions/{id}   # Delete session (Manager/Tester)
POST   /chat/sessions/{id}/messages/stream # Stream AI chat (Manager/Tester)
```

### 🎭 **Permission Legend**
- **Manager**: Full CRUD operations (Create, Read, Update, Delete)
- **Tester**: CRU operations (Create, Read, Update) - Cannot delete
- **Viewer**: Read-only access
- **Admin**: Full access to ALL endpoints when using admin token

## 🧪 Testing & Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/api/v1/         # API endpoint tests
pytest tests/crud/           # CRUD operation tests
```

### 🔐 **Authentication Testing Examples**

#### Admin Cross-Access Testing
```bash
# 1. Admin login (get admin token)
curl -X POST "http://127.0.0.1:8000/api/v1/admin/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# 2. Use admin token on user API (cross-access)
curl -X POST "http://127.0.0.1:8000/api/v1/projects/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Admin Test Project", "meta_data": {}, "note": "Created via admin cross-access"}'

# 3. Admin can delete (bypass Manager-only restriction)
curl -X DELETE "http://127.0.0.1:8000/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <admin_token>"
# ✅ Success - Admin bypasses role restrictions
```

#### User Role-Based Testing
```bash  
# 1. User login (role-based token)
curl -X POST "http://127.0.0.1:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tester@example.com&password=tester123"

# 2. Tester can create projects
curl -X POST "http://127.0.0.1:8000/api/v1/projects/" \
  -H "Authorization: Bearer <tester_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Tester Project", "meta_data": {}, "note": "Created by tester"}'
# ✅ Success - Testers can create

# 3. Tester cannot delete (Manager-only operation)  
curl -X DELETE "http://127.0.0.1:8000/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <tester_token>"
# ❌ 403 Forbidden - Insufficient permissions
```

#### Swagger UI Testing
```bash
# Navigate to: http://127.0.0.1:8000/docs

# Test Scenario 1: Admin Cross-Access
1. Click "Authorize" → Select "AdminOAuth2PasswordBearer"  
2. Login: admin@example.com / admin123
3. Test any user endpoint → Should succeed with full access

# Test Scenario 2: Role-Based Access
1. Click "Authorize" → Select "UserOAuth2PasswordBearer"
2. Login: viewer@example.com / viewer123  
3. Try DELETE endpoint → Should return 403 Forbidden
```

### 🏗️ **Database Management**

```bash
# Reset database with fresh test data
python manage.py reset-db

# Initialize empty database schema
python manage.py init-db  

# Seed database with test accounts only
python manage.py seed-db
```

**Note**: This project does **not** use Alembic migrations. Always use `python manage.py reset-db` after model changes.

## 🚀 Development & Deployment

### 🔧 **Environment Configuration**

Create a `.env` file in the project root:
```env
# Database Configuration
DATABASE_URL=sqlite:///./test.db

# Security Configuration  
SECRET_KEY=your-secret-key-here-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
DEBUG=True
PROJECT_NAME="GenAI Testing Assistant API"
PROJECT_DESCRIPTION="API for GenAI-powered software testing assistance platform"  
PROJECT_VERSION="1.0.0"

# CORS Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### 📦 **Adding New Features**

#### 1. Database Models
```bash
# 1. Create SQLModel in app/models/{feature}.py
# 2. Add to app/models/__init__.py imports
# 3. Run: python manage.py reset-db
```

#### 2. API Endpoints  
```bash
# 1. Create Pydantic schemas in app/schemas/{feature}.py
# 2. Implement CRUD operations in app/crud/{feature}_crud.py
# 3. Create API endpoints in app/api/v1/endpoints/{feature}.py
# 4. Add authorization: Depends(require_permissions(Permission.{FEATURE}_CREATE))
# 5. Register router in app/api/v1/api.py
```

#### 3. Authorization
```bash
# 1. Add permissions to app/core/permissions.py
# 2. Update role assignments in Permission enum
# 3. Use Depends(require_permissions(Permission.{YOUR_PERMISSION})) in endpoints
```

### 🐳 **Docker Deployment**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Initialize database on startup
RUN python manage.py reset-db

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 🏭 **Production Deployment**

```bash
# 1. Use production WSGI server
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# 2. Configure reverse proxy (Nginx example)
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 3. Environment variables for production
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export SECRET_KEY="production-secret-key"
export DEBUG=False
```

### 📋 **Code Style & Standards**

This project follows modern Python best practices:

- **🎯 Type Hints**: Full type annotation with Python 3.11+ features
- **📝 Pydantic v2**: Modern data validation and serialization  
- **🏗️ SQLModel**: Type-safe database operations
- **🔧 FastAPI Dependencies**: Proper dependency injection patterns
- **🎨 Clean Architecture**: Clear separation between API, business logic, and data layers
- **📚 Comprehensive Documentation**: Inline comments and detailed docstrings

### 🔍 **Logging & Monitoring**

The application includes comprehensive logging:

```python
import logging

# Authorization events  
logger.info(f"User {user.username} authorized with permissions: {permissions}")
logger.warning(f"User {user.username} denied access: {missing_permissions}")

# Admin cross-access
logger.info(f"Admin token detected - granting full access to user API")

# Authentication events
logger.error(f"Invalid authentication attempt: {error}")
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`  
3. **Follow coding standards**: Type hints, Pydantic validation, proper authorization
4. **Add tests**: Ensure new features have appropriate test coverage
5. **Update documentation**: Keep README and API docs current
6. **Commit changes**: `git commit -m 'Add amazing feature with proper authorization'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**: Provide clear description of changes

### 🎯 **Contribution Guidelines**

- **Authorization**: All new endpoints must use `Depends(require_permissions())`
- **Testing**: Include tests for both user roles and admin cross-access
- **Documentation**: Update Swagger descriptions and permission requirements
- **Type Safety**: Use proper type hints and Pydantic schemas
- **Security**: Follow the established dual authentication pattern

## 📚 Additional Documentation

- **📖 [Complete Authorization System](docs/authorization-system.md)** - Comprehensive guide to permissions, roles, and admin cross-access
- **💬 [Chat API Documentation](docs/chat-api-documentation.md)** - AI conversation system reference
- **📁 [File Management API](docs/file_editing_api.md)** - File operations and project structure
- **🔧 [Development Logs](docs/logs.md)** - Technical implementation history

## 🔗 Quick Links

- **🎯 API Documentation**: http://127.0.0.1:8000/docs (with cross-token auth)
- **📚 Alternative Docs**: http://127.0.0.1:8000/redoc  
- **⚡ OpenAPI Schema**: http://127.0.0.1:8000/openapi.json
- **🏠 Health Check**: http://127.0.0.1:8000/health

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **🐛 Bug Reports**: Open an issue on GitHub with detailed reproduction steps
- **💡 Feature Requests**: Describe the feature and its use case in a GitHub issue
- **❓ Questions**: Check existing documentation or create a discussion thread
- **🔐 Security Issues**: Report privately to maintainers

---

**🚀 Built with FastAPI + SQLModel + LangGraph | 🔐 Dual Authentication | 🤖 AI-Powered Testing Assistant**