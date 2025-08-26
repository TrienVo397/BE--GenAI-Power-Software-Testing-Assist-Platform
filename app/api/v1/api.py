from fastapi import APIRouter
from app.api.v1.endpoints import users, projects, document_versions, project_artifacts, files, chat, admin, project_members

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(project_members.router, prefix="", tags=["project_members"])  # No prefix since routes already include /projects/{id}/members
api_router.include_router(document_versions.router, prefix="/document-versions", tags=["document_versions"])
api_router.include_router(project_artifacts.router, prefix="/project-artifacts", tags=["project_artifacts"])
api_router.include_router(files.router, prefix="/projects", tags=["files"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])