from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    project_name: str = "FastAPI SQLModel Backend"
    project_description: str = "A FastAPI backend with SQLModel"
    project_version: str = "1.0.0"
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    debug: bool = True
    allowed_hosts: str = "localhost,127.0.0.1"

    class Config:
        env_file = ".env"

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert comma-separated allowed hosts to list"""
        return [host.strip() for host in self.allowed_hosts.split(",")]

settings = Settings()