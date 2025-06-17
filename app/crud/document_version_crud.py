from sqlmodel import Session, select
from typing import List, Optional
import uuid

from app.models.document_version import DocumentVersion
from app.models.project import Project
from app.schemas.document_version import DocumentVersionCreate, DocumentVersionUpdate

class DocumentVersionCRUD:
    def create(self, db: Session, *, doc_version: DocumentVersionCreate) -> DocumentVersion:
        db_doc_version = DocumentVersion(
            project_id=doc_version.project_id,
            version_label=doc_version.version_label,
            is_current=doc_version.is_current,
            created_by=doc_version.created_by,
            updated_by=doc_version.updated_by
        )
        
        # If this version is marked as current, update all other versions for this project
        if doc_version.is_current:
            self._update_current_version_status(db, doc_version.project_id, None)
        
        db.add(db_doc_version)
        db.commit()
        db.refresh(db_doc_version)
        return db_doc_version

    def get(self, db: Session, doc_version_id: uuid.UUID) -> Optional[DocumentVersion]:
        return db.get(DocumentVersion, doc_version_id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[DocumentVersion]:
        return db.exec(select(DocumentVersion).offset(skip).limit(limit)).all()
        
    def get_by_project(
        self, db: Session, *, project_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DocumentVersion]:
        return db.exec(select(DocumentVersion)
                      .where(DocumentVersion.project_id == project_id)
                      .offset(skip)
                      .limit(limit)).all()

    def get_current_version(
        self, db: Session, *, project_id: uuid.UUID
    ) -> Optional[DocumentVersion]:
        project = db.get(Project, project_id)
        if not project or not project.current_version:
            return None
        return db.get(DocumentVersion, project.current_version)

    def update(
        self, db: Session, *, doc_version: DocumentVersionUpdate, doc_version_id: uuid.UUID
    ) -> DocumentVersion:
        db_doc_version = self.get(db, doc_version_id)
        if not db_doc_version:
            return None
            
        update_data = doc_version.model_dump(exclude_unset=True)
        
        # Handle is_current status change
        if "is_current" in update_data and update_data["is_current"]:
            self._update_current_version_status(db, db_doc_version.project_id, doc_version_id)
            
        for key, value in update_data.items():
            setattr(db_doc_version, key, value)
            
        db.add(db_doc_version)
        db.commit()
        db.refresh(db_doc_version)
        return db_doc_version
        
    def delete(self, db: Session, *, doc_version_id: uuid.UUID) -> DocumentVersion:
        db_doc_version = self.get(db, doc_version_id)
        if not db_doc_version:
            return None
            
        db.delete(db_doc_version)
        db.commit()
        return db_doc_version
    
    def _update_current_version_status(
        self, db: Session, project_id: uuid.UUID, new_current_version_id: Optional[uuid.UUID]
    ) -> None:
        """Set all other versions of this project to is_current=False"""
        query = select(DocumentVersion).where(DocumentVersion.project_id == project_id)
        
        if new_current_version_id:
            query = query.where(DocumentVersion.id != new_current_version_id)
            
        versions = db.exec(query).all()
        
        for version in versions:
            version.is_current = False
            db.add(version)

document_version_crud = DocumentVersionCRUD()
