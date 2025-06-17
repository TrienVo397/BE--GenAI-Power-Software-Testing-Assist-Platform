from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime
import uuid

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class CRUDProject:
    def create(self, db: Session, project: ProjectCreate) -> Project:
        db_project = Project(
            name=project.name,
            repo_path=project.repo_path,
            project_metadata=project.project_metadata,
            created_by=project.created_by,
            updated_by=project.updated_by
        )
        db.add(db_project)
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
        return projects

    def update(self, db: Session, project: ProjectUpdate, project_id: uuid.UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        db_project = db.exec(statement).first()
        if db_project:
            project_data = project.dict(exclude_unset=True)
            for key, value in project_data.items():
                setattr(db_project, key, value)
            db_project.updated_at = datetime.utcnow()
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            return db_project
        return None

    def delete(self, db: Session, project_id: uuid.UUID) -> Optional[Project]:
        statement = select(Project).where(Project.id == project_id)
        project = db.exec(statement).first()
        if project:
            db.delete(project)
            db.commit()
            return project
        return None

project_crud = CRUDProject()
