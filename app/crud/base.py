# filepath: fastapi-sqlmodel-backend/app/crud/base.py

from typing import Generic, TypeVar, List, Optional
from sqlmodel import Session, select

ModelType = TypeVar("ModelType")

class CRUDBase(Generic[ModelType]):
    def __init__(self, model: ModelType):
        self.model = model

    def create(self, db: Session, obj_in: ModelType) -> ModelType:
        db.add(obj_in)
        db.commit()
        db.refresh(obj_in)
        return obj_in

    def read(self, db: Session, id: int) -> Optional[ModelType]:
        statement = select(self.model).where(self.model.id == id)
        return db.exec(statement).first()

    def read_all(self, db: Session) -> List[ModelType]:
        statement = select(self.model)
        return db.exec(statement).all()

    def update(self, db: Session, id: int, obj_in: ModelType) -> Optional[ModelType]:
        db_obj = self.read(db, id)
        if db_obj:
            for key, value in obj_in.dict(exclude_unset=True).items():
                setattr(db_obj, key, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        return None

    def delete(self, db: Session, id: int) -> Optional[ModelType]:
        db_obj = self.read(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return db_obj
        return None