from sqlmodel import Session
from app.core.database import engine
from app.models.user import User
from app.core.security import hash_password

def create_initial_users(session: Session):
    """Create 2 initial users"""
    users = [
        User(
            username="admin",
            email="admin@example.com",
            full_name="Administrator",
            hashed_password=hash_password("admin123")
        ),
        User(
            username="testuser",
            email="test@example.com", 
            full_name="Test User",
            hashed_password=hash_password("test123")
        )
    ]
    
    session.add_all(users)
    session.commit()
    print("Created 2 initial users:")
    print("- admin@example.com (password: admin123)")
    print("- test@example.com (password: test123)")

def seed_database():
    """Seed the database with initial data"""
    with Session(engine) as session:
        # Check if users already exist
        existing_users = session.query(User).first()
        if existing_users:
            print("Database already contains data. Skipping seeding.")
            return
        
        print("Seeding database with initial users...")
        create_initial_users(session)
        print("Database seeding completed!")

if __name__ == "__main__":
    seed_database()