import sys
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
import os
from functools import lru_cache
import logging

class LLMConfig(BaseSettings):
    llm_type: str # Type of LLM, e.g., "deepseek", "google", etc.
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: Optional[int] = None
    max_retries: int = 2
    api_key: Optional[SecretStr] = None  # API key for the LLM, if required
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True
    )


class Settings(BaseSettings):
    project_name: str = "FastAPI SQLModel Backend"
    project_description: str = "A FastAPI backend with SQLModel"
    project_version: str = "1.0.0"
    database_url: Optional[str] = None
    secret_key: SecretStr = SecretStr("asdfsds123456")
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    debug: bool = True
    allowed_hosts: Optional[str] = None
    
    # LLM settings
    llm: LLMConfig = LLMConfig() # type: ignore

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True
    )

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert comma-separated allowed hosts to list"""
        if not self.allowed_hosts:
            return []
        return [host.strip() for host in self.allowed_hosts.split(",")]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create a function that returns settings instance and validates required fields
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:
        logger.error(f"Fatal error loading application settings: {str(e)}")
        logger.error("Missing required environment variables. Please check your .env file.")
        sys.exit(1)


# Create the settings instance
try:
    settings = get_settings()
    
    # Log settings at startup
    logger.info("Application settings loaded:")
    logger.info(f"Project name: {settings.project_name}")
    logger.info(f"Database URL: {'*' * 8}...{'*' * 8}")  # Hide full connection string
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Allowed hosts: {settings.allowed_hosts_list}")
    logger.info(f"JWT Secret Key: {'*' * 8}")  # Hide secret key in logs
    logger.info(f"LLM Type: {settings.llm.llm_type}")
    logger.info(f"LLM Model: {settings.llm.model_name}")
    
except Exception as e:
    logger.error(f"Fatal error during application startup: {str(e)}")
    sys.exit(1)