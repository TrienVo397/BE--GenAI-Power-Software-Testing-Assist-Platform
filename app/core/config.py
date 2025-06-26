from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
from functools import lru_cache
import logging

class Settings(BaseSettings):
    project_name: str = "FastAPI SQLModel Backend"
    project_description: str = "A FastAPI backend with SQLModel"
    project_version: str = "1.0.0"
    database_url: Optional[str] = None
    secret_key: str = "asdfsds123456"
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    debug: bool = True
    allowed_hosts: Optional[str] = None

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=False
    )

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert comma-separated allowed hosts to list"""
        if not self.allowed_hosts:
            return []
        return [host.strip() for host in self.allowed_hosts.split(",")]

# Create a function that returns a fresh settings instance
def get_settings() -> Settings:
    return Settings()

# Create the settings instance - this will be cached
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Log settings at startup
logger.info("Application settings loaded:")
logger.info(f"Project name: {settings.project_name}")
logger.info(f"Database URL: {settings.database_url}")
logger.info(f"Debug mode: {settings.debug}")
logger.info(f"Allowed hosts: {settings.allowed_hosts_list}")
logger.info(f"JWT Secret Key: {'*' * len(settings.secret_key)}")  # Hide secret key in logs