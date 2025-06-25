# filepath: app/schemas/project_simple.py
from pydantic import BaseModel
from typing import Optional

class ProjectCreateSimple(BaseModel):
    name: str
    meta_data: Optional[str] = None
    note: Optional[str] = None
