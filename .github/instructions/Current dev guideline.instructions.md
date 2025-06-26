---
applyTo: '**'
---
Coding standards, domain knowledge, and preferences that AI should follow.

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
