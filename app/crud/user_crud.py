from typing import List, Optional
from sqlmodel import Session, select
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

class CRUDUser:
    def create(self, db: Session, user: UserCreate) -> User:
        hashed_password = hash_password(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get(self, db: Session, user_id: int) -> Optional[User]:
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
        return users

    def update(self, db: Session, user: UserUpdate, user_id: int) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        db_user = db.exec(statement).first()
        if db_user:
            user_data = user.dict(exclude_unset=True)
            for key, value in user_data.items():
                if key == "password":
                    setattr(db_user, "hashed_password", hash_password(value))
                else:
                    setattr(db_user, key, value)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        return None

    def delete(self, db: Session, user_id: int) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        user = db.exec(statement).first()
        if user:
            db.delete(user)
            db.commit()
            return user
        return None

user_crud = CRUDUser()