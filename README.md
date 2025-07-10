# FastAPI SQLModel Backend

A modern, production-ready FastAPI backend template built with SQLModel, providing a structured approach to building RESTful APIs with CRUD operations. Features automatic API documentation with OpenAPI and Swagger UI.

## Features

- **FastAPI**: High-performance web framework for building APIs
- **SQLModel**: Modern SQL databases with Python, designed by the creator of FastAPI
- **Automatic API Documentation**: Interactive Swagger UI and ReDoc
- **Database Migrations**: Alembic integration for database schema management
- **Authentication Ready**: JWT token-based authentication structure
- **Testing Suite**: Comprehensive test setup with pytest
- **Environment Configuration**: Pydantic settings management
- **CORS Support**: Cross-origin resource sharing configuration
- **Structured Architecture**: Clean separation of concerns
- **LangGraph Integration**: Agent orchestration using LangGraph

## Project Structure

```
BE-AI/
├── app/                     # Main application package
│   ├── __init__.py         # FastAPI app initialization
│   ├── main.py             # Application entry point
│   ├── api/                # API layer
│   │   ├── __init__.py    # API router setup
│   │   └── v1/            # API version 1
│   │       ├── __init__.py
│   │       ├── api.py      # Main API router
│   │       └── endpoints/  # API endpoints
│   │           ├── __init__.py
│   │           └── users.py    # User CRUD endpoints
│   ├── core/               # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py      # Application settings
│   │   ├── database.py    # Database connection
│   │   └── security.py    # Authentication & security
│   ├── crud/              # CRUD operations
│   │   ├── __init__.py
│   │   ├── base.py       # Base CRUD class
│   │   └── user_crud.py  # User CRUD operations
│   ├── models/            # SQLModel database models
│   │   ├── __init__.py
│   │   └── user.py       # User model
│   └── schemas/           # Pydantic schemas
│       ├── __init__.py
│       └── user.py       # User schemas
├── alembic/               # Database migrations
│   ├── env.py            # Alembic environment
│   ├── script.py.mako    # Migration template
│   └── versions/         # Migration files
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py       # Test configuration
│   └── api/              # API tests
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── test_users.py
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── alembic.ini          # Alembic configuration
└── README.md            # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip or pipenv

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd BE-AI
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy and modify the .env file
   cp .env.example .env
   ```

5. **Run database migrations:**
   # Initialize the database tables
   python manage.py init-db

   # Seed the database with initial users
   python manage.py seed-db

6. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, you can access:

- **Interactive API docs (Swagger UI)**: http://127.0.0.1:8000/docs
- **Alternative API docs (ReDoc)**: http://127.0.0.1:8000/redoc
- **OpenAPI schema**: http://127.0.0.1:8000/openapi.json

## API Endpoints

### Users
- `GET /api/v1/users/` - List all users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

## Configuration

Environment variables can be configured in the `.env` file:

```env
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=abcdefg123456
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/api/v1/test_users.py
```

## Database Migrations

This project uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

## Development

### Adding New Endpoints

1. Create the SQLModel in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement CRUD operations in `app/crud/`
4. Create API endpoints in `app/api/v1/endpoints/`
5. Add the router to `app/api/v1/api.py`

### Code Style

This project follows Python best practices:

- **PEP 8** for code formatting
- **Type hints** for better code documentation
- **Pydantic models** for data validation
- **SQLModel** for database operations

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Traditional Deployment

1. Set up a production WSGI server (e.g., Gunicorn)
2. Configure environment variables
3. Set up a reverse proxy (e.g., Nginx)
4. Configure SSL certificates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you have any questions or issues, please open an issue on GitHub or contact the maintainers.