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

# Set up logging
logger = logging.getLogger(__name__)

# Try to import the coverage test function
def get_run_coverage_test():
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

@router.post("/coverage-test")
def run_coverage_analysis(
    request: CoverageTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Run coverage test analysis for a project using RTM data.
    
    This endpoint:
    1. Validates that the user is a member of the specified project
    2. Runs the coverage test analysis using requirements and RTM artifacts
    3. Returns the coverage metrics and mappings
    
    Args:
        request: CoverageTestRequest containing project_id
        
    Returns:
        Dict containing:
        - success: Boolean indicating if analysis completed
        - project_id: The project ID analyzed  
        - coverage_analysis: Dict with coverage metrics and mappings
        - message: Success message
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
        logger.info(f"Starting coverage analysis for project {project_id_str}")
        
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
