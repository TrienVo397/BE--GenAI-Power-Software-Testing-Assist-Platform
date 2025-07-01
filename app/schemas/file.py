# filepath: app/schemas/file.py
"""
Schemas for file operations
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class TextContentUpdate(BaseModel):
    """Schema for updating text file content"""
    content: str
    description: Optional[str] = None

class FileInfo(BaseModel):
    """Schema for file information"""
    name: str
    path: str
    type: str
    extension: Optional[str] = None
    size: Optional[str] = None
    last_modified: Optional[str] = None
    created: Optional[str] = None

class FileResponse(BaseModel):
    """Schema for file operation response"""
    status: str
    path: str
    size: int
    description: Optional[str] = None

class DirectoryResponse(BaseModel):
    """Schema for directory operation response"""
    status: str
    path: str

class TextFileContent(BaseModel):
    """Schema for text file content"""
    path: str
    content: str
    size: int
    extension: str

class FileListResponse(BaseModel):
    """Schema for listing files in a directory"""
    name: str
    path: str
    type: str
    size: Optional[str] = None
    extension: Optional[str] = None
