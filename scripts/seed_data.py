# filepath: scripts/seed_data.py
from sqlmodel import Session
from app.core.database import engine
from app.models.user import User
from app.models.credential import Credential
from app.core.security import hash_password

def create_initial_users(session: Session):
    """Create 2 initial users with their credentials"""
    # First create user objects
    admin_user = User(
        username="admin",
        email="admin@example.com",
        full_name="Administrator"
    )
    test_user = User(
        username="testuser",
        email="test@example.com", 
        full_name="Test User"
    )
    
    # Add users to session and flush to get IDs
    session.add(admin_user)
    session.add(test_user)
    session.flush()
      # Create credentials for each user
    if admin_user.id is None:
        raise ValueError("Admin user ID is None after flush")
    
    if test_user.id is None:
        raise ValueError("Test user ID is None after flush")
        
    admin_credential = Credential(
        user_id=admin_user.id,
        hashed_password=hash_password("admin123")
    )
    
    test_credential = Credential(
        user_id=test_user.id,
        hashed_password=hash_password("test123")
    )
    
    session.add(admin_credential)
    session.add(test_credential)
    session.commit()
    
    print("Created 2 initial users:")
    print("- admin@example.com (password: admin123)")
    print("- test@example.com (password: test123)")

def seed_database():
    """Seed the database with initial data"""
    with Session(engine) as session:
        # Check if users already exist
        from sqlmodel import select
        existing_users = session.exec(select(User)).first()
        if existing_users:
            print("Database already contains data. Skipping seeding.")
            return
        
        print("Seeding database with initial users...")
        create_initial_users(session)
        print("Database seeding completed!")

if __name__ == "__main__":
    seed_database()