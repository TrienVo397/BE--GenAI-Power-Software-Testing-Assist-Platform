# filepath: app/utils/project_fs.py
"""
Filesystem utilities for project management
"""
import os
import shutil
import subprocess
from pathlib import Path
from fastapi import UploadFile, HTTPException
import os.path
from typing import List, Dict, Optional

class ProjectFSError(Exception):
    """Custom exception for project filesystem errors"""
    pass

def create_project_directory_structure(project_id):
    """
    Creates the project directory structure in the data folder
    
    Structure:
    /project-<id>/
    ├── .git/                # Git repository
    ├── prompts/             # AI prompt templates (copied from default/prompts)
    │   └── (all files from default/prompts)
    ├── artifacts/           # Current outputs
    │   ├── requirements_traceability_matrix.md
    │   ├── test_cases.md
    │   ├── requirement.md
    ├── context/             # Context files for each artifact
    │   ├── test_cases_context.md
    │   ├── requirement_context.md
    │   └── coverage_context.md
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
    os.makedirs(project_dir / "prompts", exist_ok=True)
    os.makedirs(project_dir / "artifacts", exist_ok=True)
    os.makedirs(project_dir / "context", exist_ok=True)
    os.makedirs(project_dir / "versions" / "v0", exist_ok=True)
    
    # Copy default prompt files to project prompts
    default_prompts_dir = base_dir / "default" / "prompts"
    
    if default_prompts_dir.exists():
        # Copy entire prompts directory recursively
        for item in default_prompts_dir.rglob("*"):
            if item.is_file():
                # Get relative path from default prompts directory
                relative_path = item.relative_to(default_prompts_dir)
                target_path = project_dir / "prompts" / relative_path
                
                # Create parent directories if they don't exist
                os.makedirs(target_path.parent, exist_ok=True)
                
                # Copy the file
                shutil.copy2(item, target_path)
    else:
        # Create empty prompts directory if default doesn't exist
        with open(project_dir / "prompts" / "README.md", "w") as f:
            f.write("# Project Prompts\n\nThis directory contains prompt templates for AI agent interactions.\n")
    
    # Create empty artifact files according to the structure
    with open(project_dir / "artifacts" / "requirements_traceability_matrix.md", "w") as f:
        f.write("# Requirements Traceability Matrix\n\nThis document maps requirements to test cases and tracks their coverage.\n")
    
    with open(project_dir / "artifacts" / "test_cases.md", "w") as f:
        f.write("# Generated Test Cases\n\nThis document contains the generated test cases based on project requirements.\n")
    
    with open(project_dir / "artifacts" / "requirement.md", "w") as f:
        f.write("# Generated Requirements\n\nThis document contains the analyzed and generated requirements for the project.\n")
    
    # Create empty context files to store the context of each artifact
    with open(project_dir / "context" / "test_cases_context.md", "w") as f:
        f.write("# Test Case Context\n\nThis file contains the context and background information used to generate the test case artifact.\n")
    
    with open(project_dir / "context" / "requirement_context.md", "w") as f:
        f.write("# Requirement Context\n\nThis file contains the context and background information used to generate the requirement artifact.\n")
    
    with open(project_dir / "context" / "coverage_context.md", "w") as f:
        f.write("# Coverage Context\n\nThis file contains the context and background information used to generate the coverage analysis artifact.\n")
    
    # Initialize git repository
    try:
        # Check if git is available
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        # Initialize the repository
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        # Configure basic git settings for the repository
        subprocess.run(["git", "config", "user.name", "GenAI Platform"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "platform@example.com"], cwd=project_dir, check=True, capture_output=True)
        # Create initial commit
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial project setup"], cwd=project_dir, check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        # If git is not available or fails, create the directory anyway
        print(f"Git initialization failed: {e}. Creating .git directory manually.")
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

def get_project_base_path(project_id: str) -> Path:
    """
    Get the base path for a project
    
    Args:
        project_id: The project ID (UUID)
        
    Returns:
        Path: The path to the project directory
        
    Raises:
        ProjectFSError: If the path is invalid or doesn't exist
    """
    base_dir = Path(__file__).resolve().parents[2] / "data"
    project_dir = base_dir / f"project-{project_id}"
    
    # Security check - prevent directory traversal
    if not project_dir.resolve().is_relative_to(base_dir.resolve()):
        raise ProjectFSError("Invalid path traversal attempt")
        
    if not project_dir.exists():
        raise ProjectFSError(f"Project directory does not exist: {project_id}")
        
    return project_dir

def resolve_project_path(project_id: str, file_path: str) -> Path:
    """
    Resolve a file path within a project, ensuring it's valid
    
    Args:
        project_id: The project ID (UUID)
        file_path: The relative path within the project directory
        
    Returns:
        Path: The absolute path to the file
        
    Raises:
        ProjectFSError: If the path is invalid or outside the project directory
    """
    project_dir = get_project_base_path(project_id)
    target_path = (project_dir / file_path).resolve()
    
    # Security check - prevent directory traversal
    if not target_path.is_relative_to(project_dir):
        raise ProjectFSError(f"Invalid path: {file_path} (attempt to access outside project directory)")
        
    return target_path

def list_project_files(project_id: str, directory: Optional[str] = None, recursive: bool = True, include_hidden: bool = False) -> List[Dict]:
    """
    List files and directories in a project directory
    
    Args:
        project_id: The project ID (UUID)
        directory: Optional relative directory path within the project
        recursive: Whether to include subdirectories and their contents recursively
        include_hidden: Whether to include files/directories that start with a dot
        
    Returns:
        List[Dict]: List of file/directory information objects with name, path, type, and size
        
    Raises:
        ProjectFSError: If the path is invalid
    """
    project_dir = get_project_base_path(project_id)
    
    if directory:
        target_dir = resolve_project_path(project_id, directory)
        if not target_dir.exists():
            raise ProjectFSError(f"Directory does not exist: {directory}")
        if not target_dir.is_dir():
            raise ProjectFSError(f"Not a directory: {directory}")
    else:
        target_dir = project_dir
    
    result = []
    
    def process_directory(current_dir: Path):
        for item in current_dir.iterdir():
            # Skip hidden files/directories if not included
            if not include_hidden and item.name.startswith('.'):
                continue
                
            # Get relative path from project root
            rel_path = str(item.relative_to(project_dir))
            
            file_info = {
                "name": item.name,
                "path": rel_path,
                "type": "directory" if item.is_dir() else "file",
            }
              # Add file size for files
            if item.is_file():
                file_info["size"] = str(item.stat().st_size)  # Convert to string to ensure compatibility
                file_info["extension"] = item.suffix.lower()[1:] if item.suffix else ""
                
            result.append(file_info)
            
            # Recursively process subdirectories if requested
            if recursive and item.is_dir():
                process_directory(item)
    
    # Start processing from the target directory
    process_directory(target_dir)
    
    return result

def read_project_file(project_id: str, file_path: str) -> bytes:
    """
    Read a file from the project directory
    
    Args:
        project_id: The project ID (UUID)
        file_path: The relative path to the file within the project
        
    Returns:
        bytes: The file contents
        
    Raises:
        ProjectFSError: If the file doesn't exist or is a directory
    """
    target_path = resolve_project_path(project_id, file_path)
    
    if not target_path.exists():
        raise ProjectFSError(f"File does not exist: {file_path}")
        
    if target_path.is_dir():
        raise ProjectFSError(f"Cannot read a directory as a file: {file_path}")
        
    return target_path.read_bytes()

def save_project_file(project_id: str, file_path: str, file_content: bytes) -> str:
    """
    Save a file to the project directory
    
    Args:
        project_id: The project ID (UUID)
        file_path: The relative path to save the file to
        file_content: The file content as bytes
        
    Returns:
        str: The path where the file was saved
        
    Raises:
        ProjectFSError: If the directory doesn't exist or path is invalid
    """
    target_path = resolve_project_path(project_id, file_path)
    
    # Create parent directories if they don't exist
    os.makedirs(target_path.parent, exist_ok=True)
    
    # Write the file
    target_path.write_bytes(file_content)
    
    return str(target_path.relative_to(get_project_base_path(project_id)))

def delete_project_file(project_id: str, file_path: str) -> bool:
    """
    Delete a file or directory from the project
    
    Args:
        project_id: The project ID (UUID)
        file_path: The relative path to delete
        
    Returns:
        bool: True if deletion was successful
        
    Raises:
        ProjectFSError: If the file doesn't exist or path is invalid
    """
    target_path = resolve_project_path(project_id, file_path)
    
    if not target_path.exists():
        raise ProjectFSError(f"Path does not exist: {file_path}")
    
    # Delete the file or directory
    if target_path.is_dir():
        shutil.rmtree(target_path)
    else:
        os.remove(target_path)
    
    return True

def create_project_directory(project_id: str, directory_path: str) -> str:
    """
    Create a new directory in the project
    
    Args:
        project_id: The project ID (UUID)
        directory_path: The relative path for the new directory
        
    Returns:
        str: The path of the created directory
        
    Raises:
        ProjectFSError: If the path is invalid or already exists as a file
    """
    target_path = resolve_project_path(project_id, directory_path)
    
    if target_path.exists() and not target_path.is_dir():
        raise ProjectFSError(f"Path already exists as a file: {directory_path}")
    
    os.makedirs(target_path, exist_ok=True)
    
    return str(target_path.relative_to(get_project_base_path(project_id)))
