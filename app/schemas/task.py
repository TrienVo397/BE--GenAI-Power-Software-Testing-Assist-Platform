# filepath: app/schemas/task.py
"""
Pydantic schemas for background task management.
Contains minimal schemas needed by bot endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.tasks import TaskStatus

class TaskResponse(BaseModel):
    """Schema for task information response"""
    task_id: str = Field(..., description="Unique task identifier")
    user_id: str = Field(..., description="ID of user who created the task")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    task_type: str = Field(..., description="Type of task")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="When task was created")
    started_at: Optional[datetime] = Field(None, description="When task started executing")
    completed_at: Optional[datetime] = Field(None, description="When task completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: Optional[Dict[str, Any]] = Field(None, description="Current progress information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "project_id": "proj456",
                "task_type": "coverage_analysis",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z", 
                "completed_at": "2024-01-15T10:35:00Z",
                "result": {
                    "coverage_report": "coverage_report.html",
                    "coverage_percentage": 85.7
                },
                "error": None,
                "progress": {
                    "current_step": "completed",
                    "total_steps": 3,
                    "percentage": 100
                }
            }
        }
    }

class CoverageAnalysisRequest(BaseModel):
    """Schema for coverage analysis task parameters"""
    project_id: str = Field(..., description="Project ID to analyze coverage for")
    file_path: Optional[str] = Field(None, description="Specific file to analyze (optional)")
    analysis_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional options for coverage analysis"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": "proj-123",
                "file_path": "src/main.py",
                "analysis_options": {
                    "include_branch_coverage": True,
                    "min_coverage_threshold": 80
                }
            }
        }
    }
