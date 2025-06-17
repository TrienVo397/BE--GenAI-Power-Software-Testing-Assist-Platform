from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.project_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI SQLModel backend!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}