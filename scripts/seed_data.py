# filepath: scripts/seed_data.py
from sqlmodel import Session
from app.core.database import engine
from app.models.user import User
from app.models.admin import Admin
from app.models.credential import Credential
from app.models.admin_credential import AdminCredential
from app.core.security import hash_password

def create_initial_admins(session: Session):
    """Create initial admin users with admin credentials - all admins have full access"""
    # Create first admin
    first_admin = Admin(
        admin_username="admin",
        admin_email="admin@example.com",
        full_name="System Administrator",
        department="IT",
        created_by=None,
        linked_user_id=None
    )
    
    # Create second admin
    second_admin = Admin(
        admin_username="admin2",
        admin_email="admin2@example.com", 
        full_name="Administrator 2",
        department="IT",
        created_by=None,
        linked_user_id=None
    )
    
    # Add admins to session and flush to get IDs
    session.add(first_admin)
    session.add(second_admin)
    session.flush()
    
    # Create admin credentials
    if first_admin.id is None:
        raise ValueError("First admin ID is None after flush")
    
    if second_admin.id is None:
        raise ValueError("Second admin ID is None after flush")
        
    first_admin_credential = AdminCredential(
        admin_id=first_admin.id,
        hashed_password=hash_password("admin123")
    )
    
    second_admin_credential = AdminCredential(
        admin_id=second_admin.id,
        hashed_password=hash_password("admin123")
    )
    
    session.add(first_admin_credential)
    session.add(second_admin_credential)
    
    print("Created admin users:")
    print("- admin@example.com (password: admin123) [FULL ACCESS]")
    print("- admin2@example.com (password: admin123) [FULL ACCESS]")
    
    return first_admin, second_admin

def create_initial_users(session: Session):
    """Create initial regular users with their credentials"""
    # Create manager user
    manager_user = User(
        username="manager",
        email="manager@example.com",
        full_name="Project Manager",
        roles='["manager"]'
    )
    
    # Create tester user
    tester_user = User(
        username="tester",
        email="tester@example.com", 
        full_name="Test Engineer",
        roles='["tester"]'
    )
    
    # Create viewer user
    viewer_user = User(
        username="viewer",
        email="viewer@example.com",
        full_name="Test Viewer",
        roles='["viewer"]'
    )
    
    # Add users to session and flush to get IDs
    session.add(manager_user)
    session.add(tester_user)
    session.add(viewer_user)
    session.flush()
    
    # Create credentials for each user
    if manager_user.id is None:
        raise ValueError("Manager user ID is None after flush")
    
    if tester_user.id is None:
        raise ValueError("Tester user ID is None after flush")
        
    if viewer_user.id is None:
        raise ValueError("Viewer user ID is None after flush")
        
    manager_credential = Credential(
        user_id=manager_user.id,
        hashed_password=hash_password("manager123")
    )
    
    tester_credential = Credential(
        user_id=tester_user.id,
        hashed_password=hash_password("tester123")
    )
    
    viewer_credential = Credential(
        user_id=viewer_user.id,
        hashed_password=hash_password("viewer123")
    )
    
    session.add(manager_credential)
    session.add(tester_credential)
    session.add(viewer_credential)
    
    print("Created regular users:")
    print("- manager@example.com (password: manager123) [MANAGER]")
    print("- tester@example.com (password: tester123) [TESTER]")
    print("- viewer@example.com (password: viewer123) [VIEWER]")

def seed_database():
    """Seed the database with initial data"""
    with Session(engine) as session:
        # Check if admins or users already exist
        from sqlmodel import select
        existing_admins = session.exec(select(Admin)).first()
        existing_users = session.exec(select(User)).first()
        
        if existing_admins or existing_users:
            print("Database already contains data. Skipping seeding.")
            return
        
        print("Seeding database with initial data...")
        
        # Create admin users first
        create_initial_admins(session)
        
        # Create regular users
        create_initial_users(session)
        
        # Commit all changes
        session.commit()
        
        print("Database seeding completed!")
        print("\nAdmin Authentication: Use /api/v1/admin/login")
        print("User Authentication: Use /api/v1/users/login")
        print("Note: All authenticated admins have full access to all admin APIs")
        print("Note: Only admins can create new users via /api/v1/admin/users/create")

if __name__ == "__main__":
    seed_database()