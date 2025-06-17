from fastapi import APIRouter

router = APIRouter()

from .endpoints import users

router.include_router(users.router, prefix="/users", tags=["users"])