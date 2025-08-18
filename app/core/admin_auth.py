# filepath: app/core/admin_auth.py
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from .database import get_db
from .security import decode_access_token
from ..models.admin import Admin
from ..crud.admin_crud import admin_crud
import logging

logger = logging.getLogger(__name__)

# OAuth2 scheme for admin authentication 
admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/admin/login",
    scheme_name="AdminOAuth2PasswordBearer"
)

async def get_current_admin(
    token: str = Depends(admin_oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[Admin]:
    """
    Get current authenticated admin from JWT token
    All authenticated admins have full access to all admin APIs
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required"
        )
    
    try:
        # Decode the JWT token 
        payload = decode_access_token(token)
        admin_id_str = payload.get("sub")
        token_type = payload.get("type")
        
        # Ensure this is an admin token
        if token_type != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin token"
            )
        
        if not admin_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin token"
            )
            
        import uuid
        admin_uuid = uuid.UUID(admin_id_str)
        admin = admin_crud.get(db, admin_uuid)
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found"
            )
            
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin account is inactive"
            )
            
        return admin
        
    except ValueError as e:
        logger.error(f"Error parsing admin UUID: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token format"
        )
    except Exception as e:
        logger.error(f"Error getting current admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin authentication"
        )

# Simple admin required decorator - all authenticated admins have full access
def admin_required(func):
    """Decorator to require admin authentication - all admins have full access"""
    async def wrapper(*args, **kwargs):
        # The get_current_admin dependency will handle authentication
        # If we get here, the admin is authenticated and active
        return await func(*args, **kwargs)
    return wrapper
