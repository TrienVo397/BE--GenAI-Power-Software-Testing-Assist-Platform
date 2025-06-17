import click
from sqlmodel import Session
from app.core.database import engine, create_db_and_tables
from scripts.seed_data import seed_database

@click.group()
def cli():
    """Database management commands"""
    pass

@cli.command("init-db")
def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    create_db_and_tables()
    print("Database tables created successfully!")

@cli.command("seed-db")
def seed_db():
    """Seed database with initial users"""
    seed_database()

@cli.command("reset-db")
def reset_db():
    """Reset database (drops and recreates tables with initial users)"""
    print("Dropping all tables...")
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    
    print("Creating tables...")
    create_db_and_tables()
    
    print("Seeding with initial users...")
    seed_database()
    
    print("Database reset completed!")

if __name__ == "__main__":
    cli()