# filepath: app/crud/admin_crud.py
from typing import List, Optional
from sqlmodel import Session, select
from app.models.admin import Admin
import uuid
from datetime import datetime, timezone

class CRUDAdmin:
    def create(self, db: Session, admin_data: dict, created_by: Optional[uuid.UUID] = None) -> Admin:
        """Create a new admin - all admins have full access"""
        db_admin = Admin(
            admin_username=admin_data["admin_username"],
            admin_email=admin_data["admin_email"],
            full_name=admin_data.get("full_name"),
            department=admin_data.get("department"),
            notes=admin_data.get("notes"),
            created_by=created_by,
            linked_user_id=admin_data.get("linked_user_id")
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        
        return db_admin

    def get(self, db: Session, admin_id: uuid.UUID) -> Optional[Admin]:
        """Get admin by ID"""
        statement = select(Admin).where(Admin.id == admin_id)
        admin = db.exec(statement).first()
        return admin

    def get_by_username(self, db: Session, admin_username: str) -> Optional[Admin]:
        """Get admin by username"""
        statement = select(Admin).where(Admin.admin_username == admin_username)
        admin = db.exec(statement).first()
        return admin

    def get_by_email(self, db: Session, admin_email: str) -> Optional[Admin]:
        """Get admin by email"""
        statement = select(Admin).where(Admin.admin_email == admin_email)
        admin = db.exec(statement).first()
        return admin
    
    def get_by_username_or_email(self, db: Session, identifier: str) -> Optional[Admin]:
        """Get admin by username or email - useful for login"""
        # Try username first
        statement = select(Admin).where(Admin.admin_username == identifier)
        admin = db.exec(statement).first()
        if admin:
            return admin
        
        # Try email if username didn't match
        statement = select(Admin).where(Admin.admin_email == identifier)
        admin = db.exec(statement).first()
        return admin
    
    def get_by_linked_user(self, db: Session, user_id: uuid.UUID) -> Optional[Admin]:
        """Get admin by linked user ID"""
        statement = select(Admin).where(Admin.linked_user_id == user_id)
        admin = db.exec(statement).first()
        return admin
        
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Admin]:
        """Get multiple admins"""
        statement = select(Admin).offset(skip).limit(limit)
        admins = db.exec(statement).all()
        return list(admins)
    
    def get_active_admins(self, db: Session, skip: int = 0, limit: int = 100) -> List[Admin]:
        """Get only active admins"""
        statement = select(Admin).where(Admin.is_active == True).offset(skip).limit(limit)
        admins = db.exec(statement).all()
        return list(admins)

    def update(self, db: Session, admin_id: uuid.UUID, admin_data: dict) -> Optional[Admin]:
        """Update admin"""
        statement = select(Admin).where(Admin.id == admin_id)
        db_admin = db.exec(statement).first()
        
        if db_admin:
            # Update allowed fields
            allowed_fields = {
                'admin_username', 'admin_email', 'full_name', 'department', 
                'notes', 'is_active', 'linked_user_id', 'last_login', 'last_password_change'
            }
            
            for key, value in admin_data.items():
                if key in allowed_fields and value is not None:
                    setattr(db_admin, key, value)
            
            # Update timestamp
            db_admin.updated_at = datetime.now(timezone.utc)
            
            db.add(db_admin)
            db.commit()
            db.refresh(db_admin)
            
            return db_admin
        return None

    def delete(self, db: Session, admin_id: uuid.UUID) -> Optional[Admin]:
        """Delete admin"""
        statement = select(Admin).where(Admin.id == admin_id)
        admin = db.exec(statement).first()
        if admin:
            db.delete(admin)
            db.commit()
            return admin
        return None
    
    def activate(self, db: Session, admin_id: uuid.UUID) -> Optional[Admin]:
        """Activate admin account"""
        return self.update(db, admin_id, {"is_active": True})
    
    def deactivate(self, db: Session, admin_id: uuid.UUID) -> Optional[Admin]:
        """Deactivate admin account"""
        return self.update(db, admin_id, {"is_active": False})
    
    def update_last_login(self, db: Session, admin_id: uuid.UUID) -> Optional[Admin]:
        """Update last login timestamp"""
        return self.update(db, admin_id, {"last_login": datetime.now(timezone.utc)})

admin_crud = CRUDAdmin()
