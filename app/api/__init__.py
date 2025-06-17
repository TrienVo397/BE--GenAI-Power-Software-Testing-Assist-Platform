from fastapi import APIRouter

router = APIRouter()

from .v1 import api as v1_api

router.include_router(v1_api.api_router, prefix="/v1")