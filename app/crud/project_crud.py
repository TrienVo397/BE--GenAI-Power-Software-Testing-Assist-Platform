# filepath: app/crud/project_crud.py
from typing import List, Optional, Sequence
from sqlmodel import Session, select
from datetime import datetime, timezone
import uuid

from app.models.project import Project
from app.models.document_version import DocumentVersion
from app.models.project_artifact import ProjectArtifact
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.project_fs import create_project_directory_structure, delete_project_directory

class CRUDProject:
    def create(self, db: Session, project: ProjectCreate) -> Project:
        db_project = Project(
            name=project.name,
            repo_path=project.repo_path,
            meta_data=project.meta_data,
            note=project.note,
            created_by=project.created_by,
            updated_by=project.updated_by
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        # Create the project directory structure
        project_dir = create_project_directory_structure(db_project.id)
        
        # Update the project with the repository path
        db_project.repo_path = project_dir
        db.commit()
        db.refresh(db_project)
        
        return db_project

    def get(self, db: Session, project_id: uuid.UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        project = db.exec(statement).first()
        return project

    def get_by_name(self, db: Session, name: str) -> Optional[Project]:
        statement = select(Project).where(Project.name == name)
        project = db.exec(statement).first()
        return project    

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        statement = select(Project).offset(skip).limit(limit)
        projects = db.exec(statement).all()
        return list(projects)
        
    def get_by_user(self, db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects created by a specific user with pagination"""
        statement = select(Project).where(Project.created_by == user_id).offset(skip).limit(limit)
        projects = db.exec(statement).all()
        return list(projects)

    def update(self, db: Session, project: ProjectUpdate, project_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        db_project = db.exec(statement).first()
        if db_project:
            project_data = project.model_dump(exclude_unset=True)
            
            # Check if current_version is being updated
            if "current_version" in project_data:
                new_version_id = project_data["current_version"]
                
                # Update document versions is_current status for this project
                # First, set all versions for this project to not current
                versions_to_update = db.exec(
                    select(DocumentVersion)
                    .where(DocumentVersion.project_id == project_id)
                    .where(DocumentVersion.is_current == True)
                ).all()
                
                for version in versions_to_update:
                    version.is_current = False
                    db.add(version)
                
                # Then set the new current version if one is specified
                if new_version_id:
                    new_version = db.get(DocumentVersion, new_version_id)
                    if new_version:
                        new_version.is_current = True
                        db.add(new_version)
            
            # Update project fields
            for key, value in project_data.items():
                setattr(db_project, key, value)
            
            # Update the timestamp
            db_project.updated_at = datetime.now(timezone.utc)
            
            # Update the user who made the change if provided
            if user_id:
                db_project.updated_by = user_id
                
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            return db_project
        return None

    def delete(self, db: Session, project_id: uuid.UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        db_project = db.exec(statement).first()
        if db_project:
            # Keep a copy of project data to return
            project_copy = Project(
                id=db_project.id,
                name=db_project.name,
                repo_path=db_project.repo_path,
                current_version=None,
                note=db_project.note,
                meta_data=db_project.meta_data,
                created_at=db_project.created_at,
                created_by=db_project.created_by,
                updated_at=db_project.updated_at,
                updated_by=db_project.updated_by
            )
            
            # Clear foreign key references from Project to DocumentVersion
            db_project.current_version = None
            db.add(db_project)
            
            # Set all document versions for this project to not current
            versions_to_update = db.exec(
                select(DocumentVersion)
                .where(DocumentVersion.project_id == project_id)
                .where(DocumentVersion.is_current == True)
            ).all()
            
            for version in versions_to_update:
                version.is_current = False
                db.add(version)
                
            db.flush()
            
            # First, delete all related artifacts
            artifacts_statement = select(ProjectArtifact).where(ProjectArtifact.project_id == project_id)
            artifacts = db.exec(artifacts_statement).all()
            for artifact in artifacts:
                db.delete(artifact)
            db.flush()
            
            # Then delete all document versions
            versions_statement = select(DocumentVersion).where(DocumentVersion.project_id == project_id)
            versions = db.exec(versions_statement).all()
            for version in versions:
                # Find projects that reference this version as current
                projects_with_current = select(Project).where(Project.current_version == version.id)
                projects_to_update = db.exec(projects_with_current).all()
                
                # Clear all references to this version
                for p in projects_to_update:
                    p.current_version = None
                    db.add(p)
                
                # Delete this version
                db.delete(version)
            
            db.flush()
            
            # Finally delete the project
            db.delete(db_project)
            db.commit()
            
            # Delete the project directory structure
            delete_project_directory(project_id)
            
            return project_copy
        return None

project_crud = CRUDProject()
