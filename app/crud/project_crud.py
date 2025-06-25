# filepath: app/crud/project_crud.py
from typing import List, Optional, Sequence
from sqlmodel import Session, select
from datetime import datetime, timezone
import uuid

from app.models.project import Project
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

    def update(self, db: Session, project: ProjectUpdate, project_id: uuid.UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        db_project = db.exec(statement).first()
        if db_project:
            project_data = project.dict(exclude_unset=True)
            for key, value in project_data.items():
                setattr(db_project, key, value)
            db_project.updated_at = datetime.now(timezone.utc)
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            return db_project
        return None

    def delete(self, db: Session, project_id: uuid.UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        db_project = db.exec(statement).first()
        if db_project:
            # Delete the project directory structure
            delete_project_directory(project_id)
            
            db.delete(db_project)
            db.commit()
            return db_project
        return None

project_crud = CRUDProject()
