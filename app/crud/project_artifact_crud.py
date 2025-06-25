# filepath: app/crud/project_artifact_crud.py
from typing import List, Optional
import uuid
from sqlmodel import Session, select
from app.crud.base import CRUDBase
from app.models.project_artifact import ProjectArtifact

class CRUDProjectArtifact(CRUDBase):
    def __init__(self, model):
        super().__init__(model)
        
    def create(self, db: Session, *, obj_in) -> ProjectArtifact:
        """Create a new project artifact"""
        db_obj = ProjectArtifact(
            project_id=obj_in.project_id,
            based_on_version=obj_in.based_on_version,
            artifact_type=obj_in.artifact_type,
            file_path=obj_in.file_path,
            deprecated=obj_in.deprecated,
            deprecated_reason=obj_in.deprecated_reason,
            note=obj_in.note,
            meta_data=obj_in.meta_data,
            created_by=obj_in.created_by,
            updated_by=obj_in.updated_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
        
    def get(self, db: Session, *, id: uuid.UUID) -> Optional[ProjectArtifact]:
        """Get project artifact by ID"""
        return db.exec(select(self.model).where(self.model.id == id)).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ProjectArtifact]:
        """Get multiple project artifacts with pagination"""
        result = db.exec(select(self.model).offset(skip).limit(limit)).all()
        return list(result)  # Convert to list to satisfy type checking
    
    def get_by_project_id(self, db: Session, *, project_id: uuid.UUID) -> List[ProjectArtifact]:
        """Get all artifacts for a specific project"""
        result = db.exec(select(self.model).where(self.model.project_id == project_id)).all()
        return list(result)  # Convert to list to satisfy type checking
    
    def get_by_version(self, db: Session, *, version_id: uuid.UUID) -> List[ProjectArtifact]:
        """Get all artifacts based on a specific document version"""
        result = db.exec(select(self.model).where(self.model.based_on_version == version_id)).all()
        return list(result)  # Convert to list to satisfy type checking
    
    def get_by_artifact_type(self, db: Session, *, artifact_type: str) -> List[ProjectArtifact]:
        """Get artifacts by type"""
        result = db.exec(select(self.model).where(self.model.artifact_type == artifact_type)).all()
        return list(result)  # Convert to list to satisfy type checking
    
    def update(self, db: Session, *, id: uuid.UUID, obj_in) -> Optional[ProjectArtifact]:
        """Update a project artifact"""
        db_obj = self.get(db, id=id)
        if not db_obj:
            return None
            
        # Update attributes
        if obj_in.artifact_type is not None:
            db_obj.artifact_type = obj_in.artifact_type
        if obj_in.file_path is not None:
            db_obj.file_path = obj_in.file_path
        if obj_in.deprecated is not None:
            db_obj.deprecated = obj_in.deprecated
        if obj_in.deprecated_reason is not None:
            db_obj.deprecated_reason = obj_in.deprecated_reason
        if obj_in.note is not None:
            db_obj.note = obj_in.note
        if obj_in.meta_data is not None:
            db_obj.meta_data = obj_in.meta_data
            
        # Always update the updated_by field
        db_obj.updated_by = obj_in.updated_by
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: uuid.UUID) -> Optional[ProjectArtifact]:
        """Delete a project artifact"""
        db_obj = self.get(db, id=id)
        if not db_obj:
            return None
            
        db.delete(db_obj)
        db.commit()
        return db_obj

project_artifact_crud = CRUDProjectArtifact(ProjectArtifact)
