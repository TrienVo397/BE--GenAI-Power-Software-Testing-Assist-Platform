from sqlmodel import Session, select
from typing import List, Optional, Union
import uuid
from datetime import datetime, timezone

from app.models.document_version import DocumentVersion
from app.models.project import Project
from app.models.user import User
from app.schemas.document_version import DocumentVersionCreate, DocumentVersionUpdate
from app.utils.project_fs import create_project_directory, ProjectFSError

class DocumentVersionCRUD:
    def create(self, db: Session, *, doc_version: DocumentVersionCreate, current_user: User) -> DocumentVersion:
            
        # Create the version directory using the existing function
        try:
            version_path = f"versions/{doc_version.version_label}"
            create_project_directory(str(doc_version.project_id), version_path)
        except ProjectFSError as e:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
        db_doc_version = DocumentVersion(
            project_id=doc_version.project_id,
            version_label=doc_version.version_label,
            is_current=doc_version.is_current,
            note=doc_version.note,
            meta_data=doc_version.meta_data,  # Changed from document_version_metadata
            created_by=current_user.id,
            updated_by=current_user.id
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
        result = db.exec(select(DocumentVersion).offset(skip).limit(limit)).all()
        return list(result)
        
    def get_by_project(
        self, db: Session, *, project_id: uuid.UUID
    ) -> List[DocumentVersion]:
        result = db.exec(select(DocumentVersion)
                      .where(DocumentVersion.project_id == project_id)).all()
        return list(result)

    def get_current_version(
        self, db: Session, *, project_id: uuid.UUID
    ) -> Optional[DocumentVersion]:
        result = db.exec(select(DocumentVersion)
                      .where((DocumentVersion.project_id == project_id) & 
                            (DocumentVersion.is_current == True))).first()
        return result
        
    def update(
        self, db: Session, *, doc_version_id: uuid.UUID, doc_version: DocumentVersionUpdate, current_user: User
    ) -> Optional[DocumentVersion]:
        db_doc_version = self.get(db, doc_version_id=doc_version_id)
        if not db_doc_version:
            return None
            
        # Update attributes from the input
        update_data = doc_version.model_dump(exclude_unset=True)
        
        # If version_label is being updated, create the new version directory
        if "version_label" in update_data and update_data["version_label"] != db_doc_version.version_label:
            try:
                version_path = f"versions/{update_data['version_label']}"
                create_project_directory(str(db_doc_version.project_id), version_path)
            except ProjectFSError as e:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        # If is_current is True, make other versions non-current
        if update_data.get("is_current", False):
            self._update_current_version_status(db, db_doc_version.project_id, doc_version_id)
            
        for key, value in update_data.items():
            setattr(db_doc_version, key, value)
            
        db_doc_version.updated_at = datetime.now(timezone.utc)
        db_doc_version.updated_by = current_user.id
        
        db.add(db_doc_version)
        db.commit()
        db.refresh(db_doc_version)
        return db_doc_version
    
    def _update_current_version_status(
        self, db: Session, project_id: uuid.UUID, current_version_id: Optional[uuid.UUID]
    ) -> None:
        """Helper method to update current version status for a project"""
        query = select(DocumentVersion).where(
            (DocumentVersion.project_id == project_id) & 
            (DocumentVersion.is_current == True)
        )
        if current_version_id:
            query = query.where(DocumentVersion.id != current_version_id)
            
        db_versions = db.exec(query).all()
        
        for version in db_versions:
            version.is_current = False
            db.add(version)
            
        db.commit()
    
    def delete(self, db: Session, *, doc_version_id: uuid.UUID, current_user: Optional[User] = None) -> Optional[DocumentVersion]:
        db_doc_version = self.get(db, doc_version_id=doc_version_id)
        if not db_doc_version:
            return None
            
        # Check if this version is current for any project
        projects_with_current = db.exec(select(Project).where(
            Project.current_version == doc_version_id
        )).all()
        
        # If it is, remove this version as current
        for project in projects_with_current:
            project.current_version = None
            db.add(project)
        
        db.delete(db_doc_version)
        db.commit()
        
        return db_doc_version

document_version_crud = DocumentVersionCRUD()
