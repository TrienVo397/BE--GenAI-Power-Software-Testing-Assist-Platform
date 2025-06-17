# filepath: fastapi-sqlmodel-backend/app/models/user.py
from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    full_name: Optional[str] = None
    hashed_password: str = Field(nullable=False)