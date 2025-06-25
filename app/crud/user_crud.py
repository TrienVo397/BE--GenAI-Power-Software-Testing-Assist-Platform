# filepath: app/crud/user_crud.py
from typing import List, Optional, cast
from sqlmodel import Session, select, Sequence
from app.models.user import User
from app.models.credential import Credential
import uuid
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.crud.credential_crud import credential_crud
from app.core.security import hash_password
from datetime import datetime, timezone

class CRUDUser:
    def create(self, db: Session, user: UserCreate) -> User:
        # Create user without password
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create credential for the user
        if db_user.id is not None:  # Ensure id is not None
            credential_crud.create(db=db, user_id=db_user.id, password=user.password)
        
        return db_user

    def get(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        user = db.exec(statement).first()
        return user

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        user = db.exec(statement).first()
        return user

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        user = db.exec(statement).first()
        return user
        
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        statement = select(User).offset(skip).limit(limit)
        users = db.exec(statement).all()
        return list(users)

    def update(self, db: Session, user: UserUpdate, user_id: uuid.UUID) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        db_user = db.exec(statement).first()
        if db_user:
            user_data = user.dict(exclude_unset=True)
            # Handle password update separately via credential
            password = user_data.pop("password", None)
            
            # Update user attributes
            for key, value in user_data.items():
                setattr(db_user, key, value)
            
            # Update the updated_at timestamp
            db_user.updated_at = datetime.now(timezone.utc)
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Update password if provided
            if password and db_user.id is not None:
                credential = credential_crud.get_by_user_id(db, db_user.id)
                if credential:
                    credential_crud.update(db, db_credential=credential, password=password)
            
            return db_user
        return None

    def delete(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        user = db.exec(statement).first()
        if user:
            # Delete credential first (foreign key constraint)
            credential = credential_crud.get_by_user_id(db, user_id)
            if credential:
                db.delete(credential)
                db.commit()
            
            # Then delete user
            db.delete(user)
            db.commit()
            return user
        return None

user_crud = CRUDUser()