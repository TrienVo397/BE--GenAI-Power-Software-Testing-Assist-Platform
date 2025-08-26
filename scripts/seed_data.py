# filepath: scripts/seed_data.py
from sqlmodel import Session
from app.core.database import engine
from app.models.user import User
from app.models.admin import Admin
from app.models.credential import Credential
from app.models.admin_credential import AdminCredential
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.core.security import hash_password
from app.crud.project_crud import project_crud
from app.crud.project_member_crud import project_member_crud
from app.schemas.project import ProjectCreate
from app.schemas.project_member import ProjectMemberCreate
from datetime import datetime, timezone
import uuid

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
    """Create initial regular users with their credentials - no global roles"""
    # Create user1 - will be project manager
    user1 = User(
        username="user1",
        email="user1@example.com",
        full_name="User One"
    )
    
    # Create user2 - will be project tester  
    user2 = User(
        username="user2",
        email="user2@example.com", 
        full_name="User Two"
    )
    
    # Create user3 - will be project viewer
    user3 = User(
        username="user3",
        email="user3@example.com",
        full_name="User Three"
    )
    
    # Add users to session and flush to get IDs
    session.add(user1)
    session.add(user2)
    session.add(user3)
    session.flush()
    
    # Create credentials for each user
    if user1.id is None:
        raise ValueError("User1 ID is None after flush")
    
    if user2.id is None:
        raise ValueError("User2 ID is None after flush")
        
    if user3.id is None:
        raise ValueError("User3 ID is None after flush")
        
    user1_credential = Credential(
        user_id=user1.id,
        hashed_password=hash_password("user123")
    )
    
    user2_credential = Credential(
        user_id=user2.id,
        hashed_password=hash_password("user123")
    )
    
    user3_credential = Credential(
        user_id=user3.id,
        hashed_password=hash_password("user123")
    )
    
    session.add(user1_credential)
    session.add(user2_credential)
    session.add(user3_credential)
    
    print("Created regular users:")
    print("- user1@example.com (password: user123) [No global role - project-based only]")
    print("- user2@example.com (password: user123) [No global role - project-based only]")
    print("- user3@example.com (password: user123) [No global role - project-based only]")
    
    return user1, user2, user3

def create_sample_project_with_memberships(session: Session, user1: User, user2: User, user3: User):
    """Create a sample project with user1 as manager only"""
    
    # Create project by user1
    project_create = ProjectCreate(
        name="Sample Testing Project",
        meta_data="This is a sample project for testing the GenAI platform",
        note="Created during database seeding for demonstration purposes",
        start_date=datetime.now(timezone.utc),
        created_by=user1.id,
        updated_by=user1.id
    )
    
    # Create the project using CRUD
    db_project = project_crud.create(db=session, project=project_create)
    
    # Add user1 as MANAGER (project creator)
    manager_membership = ProjectMemberCreate(
        user_id=user1.id,
        role=ProjectRole.MANAGER,
        is_active=True
    )
    project_member_crud.add_member(
        db=session,
        project_id=db_project.id,
        member_data=manager_membership,
        added_by=user1.id  # Self-assigned
    )
    
    print(f"\nCreated sample project: '{db_project.name}' (ID: {db_project.id})")
    print("Project memberships:")
    print(f"- user1 ('{user1.email}') → MANAGER [Full project control]")
    print(f"- user2 ('{user2.email}') → Not assigned to any project yet")
    print(f"- user3 ('{user3.email}') → Not assigned to any project yet")
    
    return db_project

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
        user1, user2, user3 = create_initial_users(session)
        
        # Create sample project with memberships
        sample_project = create_sample_project_with_memberships(session, user1, user2, user3)
        
        # Commit all changes
        session.commit()
        
        print("\nDatabase seeding completed!")
        print("\nAuthentication endpoints:")
        print("- Admin: Use /api/v1/admin/login")
        print("- User: Use /api/v1/users/login")
        
        print("\nSystem overview:")
        print("- All authenticated admins have full access to admin APIs")
        print("- Only admins can create new users via /api/v1/admin/users/create")
        print("- Users have no global roles - all permissions are project-based")
        print("- Project roles: MANAGER (full control), TESTER (content modification), VIEWER (read-only)")
        
        print(f"\nSample project created: '{sample_project.name}'")
        print("- Only user1 is assigned as MANAGER to the project")
        print("- user2 and user3 are available for project assignment by managers")
        print("- Test adding members via project management APIs")

if __name__ == "__main__":
    seed_database()