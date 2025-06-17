from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session