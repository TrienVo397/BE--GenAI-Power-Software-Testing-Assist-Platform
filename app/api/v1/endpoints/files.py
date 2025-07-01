# filepath: app/api/v1/endpoints/files.py
"""
API endpoints for file management in projects
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path, Query, Request, status
from fastapi.responses import Response, FileResponse
from typing import List, Optional, Dict, Any
import os
import tempfile
from uuid import UUID

from app.utils.project_fs import (
    list_project_files, read_project_file, save_project_file,
    delete_project_file, create_project_directory, ProjectFSError,
    resolve_project_path
)
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.file import TextContentUpdate, FileInfo, FileResponse, DirectoryResponse, TextFileContent, FileListResponse

router = APIRouter()

@router.get("/{project_id}/files", 
    summary="List files in project",
    response_model=List[FileListResponse])
async def list_files(
    project_id: UUID = Path(..., description="The project ID"),
    directory: Optional[str] = Query(None, description="Optional subdirectory path"),
    recursive: bool = Query(True, description="Whether to include subdirectories recursively"),
    include_hidden: bool = Query(False, description="Whether to include hidden files/directories (starting with '.')"),
    current_user: User = Depends(get_current_user)
):
    """
    List all files and directories in a project or specific directory
    
    - Set recursive=true to list all files and subdirectories recursively (default)
    - Set include_hidden=true to include files/directories that start with a dot (like .git)
    """
    try:
        return list_project_files(str(project_id), directory, recursive=recursive, include_hidden=include_hidden)
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{project_id}/files/{file_path:path}", 
    summary="Get file from project",
    response_class=Response,
    responses={
        200: {
            "description": "File content. Returns raw file or JSON with text content when as_json=true",
            "content": {
                "application/json": {
                    "example": {"path": "example.md", "content": "# Example", "size": 9, "extension": "md"}
                },
                "application/octet-stream": {},
                "text/plain": {},
                "image/jpeg": {},
                "image/png": {},
                "application/pdf": {},
            },
        }
    })
async def get_file(
    project_id: UUID = Path(..., description="The project ID"),
    file_path: str = Path(..., description="Path to file within project directory"),
    as_json: bool = Query(False, description="If true and file is text, returns content as JSON instead of raw file"),
    current_user: User = Depends(get_current_user)
):
    """
    Get the contents of a file from the project directory
    
    This endpoint will return the file with the appropriate content type:
    - Text files (.txt, .md, .yml, .yaml) as text/plain
    - JSON files as application/json
    - HTML files as text/html
    - Images (.jpg, .png) as image/jpeg or image/png
    - PDF files as application/pdf
    - All other files as application/octet-stream
    
    Parameters:
    - as_json: If set to true and the file is a text file, returns the content as JSON 
      with the content as a string field. Useful for editing text files in a UI.
    """
    try:
        file_content = read_project_file(str(project_id), file_path)
        
        # Determine content type based on file extension
        content_type = "application/octet-stream"  # Default binary content type
        extension = os.path.splitext(file_path)[1].lower()
        
        # List of text file extensions
        text_extensions = ['.txt', '.md', '.yml', '.yaml', '.json', '.csv', '.html', '.js', '.py', '.xml']
        is_text_file = any(extension == ext for ext in text_extensions)
        
        if extension in (".txt", ".md", ".yml", ".yaml"):
            content_type = "text/plain"
        elif extension == ".json":
            content_type = "application/json"
        elif extension == ".html":
            content_type = "text/html"
        elif extension in (".jpg", ".jpeg"):
            content_type = "image/jpeg"
        elif extension == ".png":
            content_type = "image/png"
        elif extension == ".pdf":
            content_type = "application/pdf"
            
        # If requested as JSON and it's a text file
        if as_json and is_text_file:
            try:
                text_content = file_content.decode('utf-8')
                text_file_content = TextFileContent(
                    path=file_path,
                    content=text_content,
                    size=len(file_content),
                    extension=extension[1:] if extension else ""
                )
                # Return as JSON response, not as a pydantic model directly
                return Response(
                    content=text_file_content.json(),
                    media_type="application/json"
                )
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The file does not appear to be a valid text file"
                )
        
        # Otherwise return raw file
        filename = os.path.basename(file_path)
        return Response(
            content=file_content, 
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{project_id}/files/{file_path:path}", 
    summary="Upload file to project",
    status_code=status.HTTP_201_CREATED,
    response_model=FileResponse)
async def upload_file(
    project_id: UUID = Path(..., description="The project ID"),
    file_path: str = Path(..., description="Path where to save the file"),
    file: UploadFile = File(..., description="File to upload"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file to the project directory
    
    Note: For updating existing files, consider using the PUT endpoint which supports
    both file uploads and text content updates.
    """
    try:
        # Read the file content
        file_content = await file.read()
        
        # Save the file
        saved_path = save_project_file(str(project_id), file_path, file_content)
        
        return FileResponse(
            status="success",
            path=saved_path,
            size=len(file_content)
        )
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{project_id}/files/{file_path:path}", 
    summary="Delete file from project")
async def delete_file(
    project_id: UUID = Path(..., description="The project ID"),
    file_path: str = Path(..., description="Path to file or directory to delete"),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file or directory from the project
    """
    try:
        delete_project_file(str(project_id), file_path)
        return {"status": "success", "message": f"Deleted {file_path}"}
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{project_id}/directories/{directory_path:path}", 
    summary="Create directory in project",
    status_code=status.HTTP_201_CREATED,
    response_model=DirectoryResponse)
async def create_directory(
    project_id: UUID = Path(..., description="The project ID"),
    directory_path: str = Path(..., description="Path for the new directory"),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new directory in the project
    """
    try:
        created_path = create_project_directory(str(project_id), directory_path)
        return DirectoryResponse(status="success", path=created_path)
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{project_id}/files/{file_path:path}/info", 
    summary="Get file information",
    response_model=Dict[str, Any])
async def get_file_info(
    project_id: UUID = Path(..., description="The project ID"),
    file_path: str = Path(..., description="Path to file within project directory"),
    current_user: User = Depends(get_current_user)
):
    """
    Get information about a file or directory without downloading its contents
    
    Returns metadata such as:
    - size (for files)
    - type (file or directory)
    - last modified time
    - for directories, returns a list of immediate children
    """
    try:
        import os
        from datetime import datetime
        
        target_path = resolve_project_path(str(project_id), file_path)
        
        if not target_path.exists():
            raise ProjectFSError(f"Path does not exist: {file_path}")
            
        # Get common file info
        stat_info = target_path.stat()
        result: Dict[str, Any] = {
            "name": target_path.name,
            "path": file_path,
            "type": "directory" if target_path.is_dir() else "file",
            "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
        }
        
        # Add file-specific info
        if target_path.is_file():
            result.update({
                "size": str(stat_info.st_size),
                "extension": target_path.suffix.lower()[1:] if target_path.suffix else "",
            })
        
        # Add directory-specific info
        elif target_path.is_dir():
            children = []
            for child in target_path.iterdir():
                # Skip hidden files/directories
                if child.name.startswith('.'):
                    continue
                    
                child_info = {
                    "name": child.name,
                    "type": "directory" if child.is_dir() else "file",
                }
                
                if child.is_file():
                    child_info["size"] = str(child.stat().st_size)
                    child_info["extension"] = child.suffix.lower()[1:] if child.suffix else ""
                
                children.append(child_info)
                
            result["children"] = children
            result["count"] = len(children)
            
        return result
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Split PUT endpoint into two separate functions based on content type
# 1. For text file updates via JSON
@router.put("/{project_id}/files/{file_path:path}", 
    summary="Update file content with JSON",
    response_model=FileResponse,
    responses={
        200: {"description": "File updated successfully"},
        400: {"description": "Invalid request or unsupported file type"},
        404: {"description": "File not found"}
    })
async def update_file_text(
    text_update: TextContentUpdate,
    project_id: UUID = Path(..., description="The project ID"),
    file_path: str = Path(..., description="Path to the file within project directory"),
    current_user: User = Depends(get_current_user)
):
    """
    Update a text file with JSON content
    
    This endpoint accepts a JSON payload with the new content as a string.
    
    Supported file extensions include:
    - Markdown (.md)
    - YAML (.yml, .yaml)
    - Text (.txt)
    - JSON (.json)
    - And other text-based formats (.csv, .html, .js, .py, .xml)
    """
    try:
        # Validate file extension to ensure it's a text file
        extension = os.path.splitext(file_path)[1].lower()
        allowed_extensions = ['.md', '.yml', '.yaml', '.txt', '.json', '.csv', '.html', '.js', '.py', '.xml']
        
        if not any(extension == ext for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"File type not supported for text editing. Supported extensions: {', '.join(allowed_extensions)}"
            )
        
        # Convert text content to bytes
        file_content = text_update.content.encode('utf-8')
        description = text_update.description
        
        # Save the updated file
        saved_path = save_project_file(str(project_id), file_path, file_content)
        
        return FileResponse(
            status="success",
            path=saved_path,
            size=len(file_content),
            description=description
        )
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# 2. For file uploads via form data
@router.put("/{project_id}/files/{file_path:path}/upload", 
    summary="Update file content with upload",
    response_model=FileResponse,
    responses={
        200: {"description": "File uploaded successfully"},
        400: {"description": "Invalid request"},
        404: {"description": "File not found"}
    })
async def update_file_upload(
    project_id: UUID = Path(..., description="The project ID"),
    file_path: str = Path(..., description="Path to the file within project directory"),
    file: UploadFile = File(..., description="File to upload"),
    current_user: User = Depends(get_current_user)
):
    """
    Update a file by uploading a new version
    
    This endpoint accepts a file upload as multipart/form-data.
    Use this for any file type, including binary files.
    """
    try:
        # Read the file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Save the updated file
        saved_path = save_project_file(str(project_id), file_path, file_content)
        
        return FileResponse(
            status="success",
            path=saved_path,
            size=len(file_content)
        )
    except ProjectFSError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
