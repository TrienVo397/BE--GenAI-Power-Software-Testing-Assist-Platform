# filepath: app/utils/project_fs.py
"""
Filesystem utilities for project management
"""
import os
import shutil
import subprocess
from pathlib import Path

class ProjectFSError(Exception):
    """Custom exception for project filesystem errors"""
    pass

def create_project_directory_structure(project_id):
    """
    Creates the project directory structure in the data folder
    
    Structure:
    /project-<id>/
    ├── .git/                # Git repository
    ├── templates/           # Version-controlled templates
    │   ├── checklist.yml    # YAML template
    │   └── testcase.yml
    ├── artifacts/           # Current outputs
    │   ├── checklist.md
    │   └── testcases.md
    └── versions/            # Versioned documents
        ├── v0/
        │   └── srs.pdf
        ├── v1/
        │   └── srs.pdf
        └── v2/
            └── srs.pdf
    
    Args:
        project_id: The project ID (UUID)
        
    Returns:
        str: The path to the created project directory
    """
    # Get the base directory from the application root
    base_dir = Path(__file__).resolve().parents[2] / "data"
    
    # Create the project directory
    project_dir = base_dir / f"project-{project_id}"
    
    # Security check - prevent directory traversal
    if not project_dir.resolve().is_relative_to(base_dir.resolve()):
        raise ProjectFSError("Invalid path traversal attempt")
        
    # Create the main directory structure
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(project_dir / "templates", exist_ok=True)
    os.makedirs(project_dir / "artifacts", exist_ok=True)
    os.makedirs(project_dir / "versions" / "v0", exist_ok=True)
    os.makedirs(project_dir / "versions" / "v1", exist_ok=True)
    os.makedirs(project_dir / "versions" / "v2", exist_ok=True)
    
    # Create empty template files
    with open(project_dir / "templates" / "checklist.yml", "w") as f:
        f.write("# Checklist template\n")
    
    with open(project_dir / "templates" / "testcase.yml", "w") as f:
        f.write("# Test case template\n")
    
    # Create empty artifact files
    with open(project_dir / "artifacts" / "checklist.md", "w") as f:
        f.write("# Generated Checklist\n")
    
    with open(project_dir / "artifacts" / "testcases.md", "w") as f:
        f.write("# Generated Test Cases\n")
    
    # Initialize git repository
    try:
        subprocess.run(["git", "init"], cwd=project_dir, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        # If git is not available, create the directory anyway
        os.makedirs(project_dir / ".git", exist_ok=True)
    
    return str(project_dir)


def delete_project_directory(project_id):
    """
    Deletes the project directory
    
    Args:
        project_id: The project ID (UUID)
    """
    base_dir = Path(__file__).resolve().parents[2] / "data"
    project_dir = base_dir / f"project-{project_id}"
    
    if project_dir.exists():
        shutil.rmtree(project_dir)
