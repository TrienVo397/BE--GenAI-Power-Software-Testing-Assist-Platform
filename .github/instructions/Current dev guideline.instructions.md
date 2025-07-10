---
applyTo: '**'
---
Coding standards, domain knowledge, and preferences that AI should follow.

## Run Python
- Run Python code in a virtual environment (venv) in the root folder to avoid conflicts with system packages.
- I will doing the terminal command manually, so no need to automate this.

## Project Structure and AI Indexing Guidelines

This is a FastAPI-based backend service for a GenAI-powered software testing assistance platform. The project follows a clean architecture pattern with clear separation of concerns.

### Core Directory Structure

- **`app/`** - Main application code
  - **`api/`** - API layer with versioned endpoints
    - **`v1/`** - Version 1 API endpoints
      - **`endpoints/`** - Individual endpoint handlers
  - **`core/`** - Core application configuration and utilities
    - `config.py` - Application configuration settings
    - `database.py` - Database connection and session management
    - `security.py` - Authentication and security utilities
  - **`crud/`** - CRUD operations for database entities
    - Each file handles database operations for a specific model
  - **`models/`** - SQLAlchemy database models
    - Define database schema and relationships
  - **`schemas/`** - Pydantic schemas for request/response validation
    - Define API input/output data structures
  - **`utils/`** - Utility functions and helpers
    - `project_fs.py` - File system operations for projects

### Data Management

- **`data/`** - Project data storage
  - **`default/templates/`** - Default project templates
  - **`project-{uuid}/`** - Individual project workspaces
    - **`artifacts/`** - Generated test artifacts
    - **`templates/`** - Project-specific templates
    - **`versions/`** - Document version history

### Supporting Files

- **`scripts/`** - Database seeding and utility scripts
- **`tests/`** - Test suite (following pytest conventions) (currently unused)
- **`alembic/`** - Database migration files (currently unused)
- `manage.py` - Database management commands
- `requirements.txt` - Python dependencies

### AI Crawling and Indexing Best Practices

When analyzing this codebase:

1. **Start with models** (`app/models/`) to understand data structures
2. **Review schemas** (`app/schemas/`) to understand API contracts
3. **Check CRUD operations** (`app/crud/`) to understand business logic
4. **Examine endpoints** (`app/api/v1/endpoints/`) to understand API functionality
5. **Look at core config** (`app/core/`) to understand system setup

### Key Relationships

- **User** → **Project** (one-to-many)
- **Project** → **ProjectArtifact** (one-to-many)
- **Project** → **DocumentVersion** (one-to-many)
- **User** → **Credential** (one-to-one)

### File Naming Conventions

- Model files: `{entity}.py` (e.g., `user.py`, `project.py`)
- CRUD files: `{entity}_crud.py` (e.g., `user_crud.py`)
- Schema files: `{entity}.py` (e.g., `user.py`, `project.py`)
- Endpoint files: `{entity}.py` or descriptive names

## Database Management

- Alembic is currently not in use for database migrations
- When making changes to database models or schema:
  - Do not create Alembic migrations
  - Simply run `python manage.py reset-db` to reset the database
  - This command will recreate the database structure based on current model definitions
  - Run this command after any database model changes to apply them
  - Do not make the test suit or file, as it is not required for this project

## Data Validation

- Use Pydantic v2 for all data validation and schema definitions
- When creating new schemas or modifying existing ones:
  - Import directly from `pydantic` (not `pydantic.v1`)
  - Utilize v2 features like computed fields and validators
  - Follow Pydantic v2 patterns for model configuration
  - Use `model_config` dict instead of the deprecated Config class
