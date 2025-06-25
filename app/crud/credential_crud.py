# filepath: app/crud/credential_crud.py
from sqlmodel import Session, select
from app.models.credential import Credential
from app.models.user import User
from app.core.security import hash_password
from typing import Optional, Dict, Any, Union
from .base import CRUDBase
from datetime import datetime, timezone
import uuid

class CRUDCredential(CRUDBase[Credential]):
    def create(self, db: Session, *, user_id: uuid.UUID, password: str) -> Credential:
        """Create a new credential for a user"""
        db_credential = Credential(
            user_id=user_id,
            hashed_password=hash_password(password),
        )
        db.add(db_credential)
        db.commit()
        db.refresh(db_credential)
        return db_credential

    def update(self, db: Session, *, db_credential: Credential, password: str = None) -> Credential:
        """Update a credential"""
        if password is not None:
            db_credential.hashed_password = hash_password(password)
        
        # Update the updated_at timestamp
        db_credential.updated_at = datetime.now(timezone.utc)
        
        db.add(db_credential)
        db.commit()
        db.refresh(db_credential)
        return db_credential
        
    def get_by_user_id(self, db: Session, user_id: uuid.UUID) -> Optional[Credential]:
        """Get credential by user_id"""
        return db.exec(select(Credential).where(Credential.user_id == user_id)).first()

credential_crud = CRUDCredential(Credential)
