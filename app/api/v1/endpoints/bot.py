# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\api\v1\endpoints\bot.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, Any
import uuid
import logging
import sys
import os
from pathlib import Path

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.bot import CoverageTestRequest
from app.schemas.task import TaskResponse, CoverageAnalysisRequest
from app.core.tasks import task_manager, TaskTypes

# Set up logging
logger = logging.getLogger(__name__)

# Try to import the coverage test function
async def get_run_coverage_test():
    """Dynamically import the run_coverage_test function"""
    try:
        # Add the ai/mcp directory to the path
        current_file_path = Path(__file__).resolve()
        ai_mcp_path = current_file_path.parent.parent.parent.parent.parent / "ai" / "mcp"
        
        if str(ai_mcp_path) not in sys.path:
            sys.path.insert(0, str(ai_mcp_path))
        
        from coverage_test_bot import run_coverage_test
        logger.info("Successfully imported coverage_test_bot")
        return run_coverage_test
    except ImportError as e:
        logger.error(f"Failed to import coverage_test_bot: {e}")
        raise ImportError(f"Cannot import coverage_test_bot module: {e}. Please ensure the coverage_test_bot.py file exists in ai/mcp/ directory.")

router = APIRouter()

@router.post("/coverage-test", response_model=TaskResponse)
async def run_coverage_analysis(
    request: CoverageTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Create a background task to run coverage test analysis for a project using RTM data.
    
    This endpoint:
    1. Validates that the user is a member of the specified project
    2. Creates a background task to run the coverage test analysis
    3. Returns the task information for tracking progress
    
    Args:
        request: CoverageTestRequest containing project_id
        
    Returns:
        TaskResponse containing:
        - task_id: Unique identifier to track the analysis
        - status: Current task status  
        - created_at: When the task was created
        - Other task metadata
    """
    # Check if user is a member of the project
    if not current_user.is_project_member(request.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run coverage analysis for this project"
        )
    
    try:
        # Create background task for coverage analysis
        project_id_str = str(request.project_id)
        
        # Create the task
        task_id = task_manager.create_task(
            task_func=_run_coverage_analysis_task,
            user_id=str(current_user.id),
            task_type=TaskTypes.COVERAGE_ANALYSIS,
            project_id=project_id_str,
            project_id_param=project_id_str
        )
        
        # Get task info to return
        task_info = task_manager.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task - task info not found"
            )
        
        logger.info(f"Created coverage analysis background task {task_id} for project {project_id_str}")
        
        return TaskResponse(
            task_id=task_info.task_id,
            user_id=task_info.user_id,
            project_id=task_info.project_id,
            task_type=task_info.task_type,
            status=task_info.status,
            created_at=task_info.created_at,
            started_at=task_info.started_at,
            completed_at=task_info.completed_at,
            result=task_info.result,
            error=task_info.error,
            progress=task_info.progress
        )
        
    except Exception as e:
        logger.error(f"Failed to create coverage analysis task for project {request.project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create coverage analysis task: {str(e)}"
        )

def _run_coverage_analysis_task(project_id_param: str):
    """Execute coverage analysis in background task"""
    try:
        logger.info(f"Starting background coverage analysis for project {project_id_param}")
        
        # Get the coverage test function
        run_coverage_test = get_run_coverage_test()
        
        # Run the coverage analysis
        coverage_results = run_coverage_test(project_id_param)
        
        logger.info(f"Coverage analysis completed successfully for project {project_id_param}")
        
        return {
            "success": True,
            "project_id": project_id_param,
            "coverage_analysis": coverage_results,
            "message": "Coverage analysis completed successfully"
        }
        
    except ImportError as e:
        logger.error(f"Coverage test module import failed for project {project_id_param}: {str(e)}")
        raise Exception(f"Coverage analysis service unavailable: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"Missing artifacts for project {project_id_param}: {str(e)}")
        raise Exception(f"Required project artifacts not found: {str(e)}. Please ensure requirement.md and requirements_traceability_matrix.md exist in the project artifacts directory.")
    except Exception as e:
        logger.error(f"Coverage analysis failed for project {project_id_param}: {str(e)}")
        raise Exception(f"Failed to run coverage analysis: {str(e)}")

# DEPRECATED: Legacy synchronous endpoint - kept for backward compatibility but marked as deprecated
@router.post("/coverage-test-sync", deprecated=True)
async def run_coverage_analysis_sync(
    request: CoverageTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    [DEPRECATED] Run coverage test analysis synchronously (blocks server).
    
    This endpoint is deprecated and may cause server blocking in multi-user environments.
    Use /coverage-test instead for background processing.
    
    Args:
        request: CoverageTestRequest containing project_id
        
    Returns:
        Dict containing coverage analysis results
    """
    # Check if user is a member of the project
    if not current_user.is_project_member(request.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run coverage analysis for this project"
        )
    
    try:
        # Get the coverage test function (with fallback)
        run_coverage_test = get_run_coverage_test()
        
        # Convert UUID to string for the coverage test function
        project_id_str = str(request.project_id)
        
        # Log the analysis start
        logger.info(f"Starting synchronous coverage analysis for project {project_id_str}")
        logger.warning(f"Using deprecated synchronous coverage analysis endpoint - consider using /coverage-test for background processing")
        
        # Run the coverage analysis
        coverage_results = run_coverage_test(project_id_str)
        
        # Log successful completion
        logger.info(f"Coverage analysis completed successfully for project {project_id_str}")
        
        return {
            "success": True,
            "project_id": project_id_str,
            "coverage_analysis": coverage_results,
            "message": "Coverage analysis completed successfully"
        }
        
    except ImportError as e:
        logger.error(f"Coverage test module import failed for project {request.project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coverage analysis service unavailable: {str(e)}"
        )
    except FileNotFoundError as e:
        logger.error(f"Missing artifacts for project {request.project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Required project artifacts not found: {str(e)}. Please ensure requirement.md and requirements_traceability_matrix.md exist in the project artifacts directory."
        )
    except Exception as e:
        logger.error(f"Coverage analysis failed for project {request.project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run coverage analysis: {str(e)}"
        )
