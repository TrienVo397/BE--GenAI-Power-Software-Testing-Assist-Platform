# filepath: tests/conftest.py
import pytest
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool
from app.core.database import get_db

@pytest.fixture(scope="session")
def db():
    # Create in-memory database for testing
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Create the database tables
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # Tables are dropped automatically when the in-memory database is closed

@pytest.fixture
def session(db):
    """Create a new database session for a test."""
    db.begin_nested()  # Start a nested transaction
    yield db
    db.rollback()  # Rollback any changes made during the test