# filepath: fastapi-sqlmodel-backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    # Drop the database tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def session(db):
    """Create a new database session for a test."""
    yield db
    db.rollback()  # Rollback any changes made during the test
    db.close()  # Close the session after the test