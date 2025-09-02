# filepath: fastapi-sqlmodel-backend/app/api/v1/endpoints/__init__.py
from fastapi import APIRouter

router = APIRouter()

from . import users, projects, document_versions, project_members

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(project_members.router, prefix="", tags=["project_members"])
router.include_router(document_versions.router, prefix="/document-versions", tags=["document_versions"])