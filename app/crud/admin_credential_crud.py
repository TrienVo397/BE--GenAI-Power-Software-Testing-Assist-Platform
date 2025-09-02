# filepath: app/crud/admin_credential_crud.py
from typing import Optional
from sqlmodel import Session, select
from app.models.admin_credential import AdminCredential
from app.core.security import hash_password, verify_password
from datetime import datetime, timezone
import uuid

class CRUDAdminCredential:
    def create(self, db: Session, admin_id: uuid.UUID, password: str) -> AdminCredential:
        """Create admin credential"""
        hashed_password = hash_password(password)
        
        db_credential = AdminCredential(
            admin_id=admin_id,
            hashed_password=hashed_password
        )
        
        db.add(db_credential)
        db.commit()
        db.refresh(db_credential)
        
        return db_credential

    def get_by_admin_id(self, db: Session, admin_id: uuid.UUID) -> Optional[AdminCredential]:
        """Get admin credential by admin ID"""
        statement = select(AdminCredential).where(AdminCredential.admin_id == admin_id)
        credential = db.exec(statement).first()
        return credential

    def verify_password(self, db: Session, admin_id: uuid.UUID, password: str) -> bool:
        """Verify admin password"""
        credential = self.get_by_admin_id(db, admin_id)
        
        if not credential:
            return False
        
        return verify_password(password, credential.hashed_password)

    def update_password(self, db: Session, admin_id: uuid.UUID, new_password: str) -> Optional[AdminCredential]:
        """Update admin password"""
        credential = self.get_by_admin_id(db, admin_id)
        
        if credential:
            credential.hashed_password = hash_password(new_password)
            credential.updated_at = datetime.now(timezone.utc)
            
            db.add(credential)
            db.commit()
            db.refresh(credential)
            
            return credential
        return None

    def delete(self, db: Session, admin_id: uuid.UUID) -> Optional[AdminCredential]:
        """Delete admin credential"""
        credential = self.get_by_admin_id(db, admin_id)
        if credential:
            db.delete(credential)
            db.commit()
            return credential
        return None

admin_credential_crud = CRUDAdminCredential()
