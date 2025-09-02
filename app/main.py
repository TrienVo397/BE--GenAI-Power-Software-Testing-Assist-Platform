from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.project_version,
)

# Custom OpenAPI schema with separate OAuth2 flows for admin and user
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom security schemes for both admin and user authentication
    openapi_schema["components"]["securitySchemes"] = {
        "AdminOAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/admin/login",
                    "scopes": {}
                }
            },
            "description": "Admin authentication - Admin tokens with full access to all user APIs"
        },
        "UserOAuth2PasswordBearer": {
            "type": "oauth2", 
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/users/login",
                    "scopes": {}
                }
            },
            "description": "User authentication - Standard user tokens for role-based access"
        }
    }
    
    # Enable cross-token support: Update security for all protected paths to accept either token type
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "security" in operation:
                # Replace existing security with both authentication options
                operation["security"] = [
                    {"UserOAuth2PasswordBearer": []},
                    {"AdminOAuth2PasswordBearer": []}
                ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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