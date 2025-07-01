# File Management API Guide

This guide explains how to use the API endpoints for managing project files, including listing, downloading, uploading, and editing text files.

## API Endpoints for File Management

### List Files in Project

```http
GET /projects/{project_id}/files?directory={optional_subdirectory}&recursive=true&include_hidden=false
```

Lists all files in a project or a specific directory within the project.

**Parameters:**
- `directory`: Optional subdirectory path (e.g., "templates")
- `recursive`: Whether to include subdirectories (default: true)
- `include_hidden`: Whether to include hidden files/directories (default: false)

**Response:**
Returns an array of file objects, each containing name, path, type, size, and extension information.

### Get File Information

```http
GET /projects/{project_id}/files/{file_path}/info
```

Returns metadata about a file or directory without downloading the content.

**Response:**
```json
{
  "name": "checklist.yml",
  "path": "templates/checklist.yml",
  "type": "file",
  "size": "1024",
  "extension": "yml",
  "last_modified": "2025-06-30T14:22:10.123456",
  "created": "2025-06-15T09:45:32.987654"
}
```

### Get File Content

```http
GET /projects/{project_id}/files/{file_path}?as_json=false
```

Downloads the file with the appropriate content type. Works for any file type.

**Parameters:**
- `as_json`: Optional. If set to `true` and the file is a text file, returns the content as JSON instead of a raw file. Default is `false`.

**Response (when as_json=false):**
Raw file content with appropriate content-type header.

**Response (when as_json=true for text files):**
```json
{
  "path": "templates/checklist.yml",
  "content": "# Checklist template\n- Item 1\n- Item 2",
  "size": 35,
  "extension": "yml"
}
```

### Upload New File

```http
POST /projects/{project_id}/files/{file_path}
```

Uploads a new file to the specified path in the project.

**Request Body:**
Multipart form data with a file field.

**Response:**
```json
{
  "status": "success",
  "path": "templates/checklist.yml",
  "size": 1024
}
```

### Update File Content

File updating is now split into two separate endpoints for better compatibility and clearer usage.

#### Update Text File with JSON

```http
PUT /projects/{project_id}/files/{file_path}
```

Updates text-based files using JSON content.

**Request:**
Content-Type: application/json
```json
{
  "content": "# Updated checklist template\n- New Item 1\n- New Item 2",
  "description": "Updated formatting and items"
}
```

**Response:**
```json
{
  "status": "success",
  "path": "templates/checklist.yml",
  "size": 51,
  "description": "Updated formatting and items"
}
```

**Note:** This endpoint only works with text-based files (md, yml, yaml, txt, json, etc.).

#### Update File with Upload

```http
PUT /projects/{project_id}/files/{file_path}/upload
```

Updates any file using multipart/form-data upload.

**Request:**
Content-Type: multipart/form-data with a file field.

**Response:**
```json
{
  "status": "success",
  "path": "templates/checklist.yml",
  "size": 1024
}
```

**Note:** This endpoint works with any file type, including binary files.

### Delete File or Directory

```http
DELETE /projects/{project_id}/files/{file_path}
```

Deletes a file or directory from the project.

**Response:**
```json
{
  "status": "success",
  "message": "Deleted templates/old_file.txt"
}
```

### Create Directory

```http
POST /projects/{project_id}/directories/{directory_path}
```

Creates a new directory in the project.

**Response:**
```json
{
  "status": "success",
  "path": "templates/new_directory"
}
```

## Supported Text File Types

The following text file types are supported for text editing operations:

- Markdown (`.md`)
- YAML (`.yml`, `.yaml`)
- Plain Text (`.txt`)
- JSON (`.json`)
- CSV (`.csv`)
- HTML (`.html`)
- JavaScript (`.js`)
- Python (`.py`)
- XML (`.xml`)

## Error Handling

The API uses standard HTTP status codes to indicate the result of operations:

- `200 OK` - The request was successful
- `201 Created` - A new resource was successfully created
- `400 Bad Request` - The request was invalid (e.g., unsupported file type for text editing)
- `404 Not Found` - The requested resource was not found
- `500 Internal Server Error` - An unexpected error occurred on the server

Error responses include a detail message explaining what went wrong:

```json
{
  "detail": "File type not supported for text editing. Supported extensions: md, yml, yaml, txt, json, csv, html, js, py, xml"
}
```

## Notes

- All API endpoints require authentication. Include your access token in the request headers.
- File paths are relative to the project root. For example, to access a file in the templates directory, use `templates/filename.yml`.
- File names and paths should be URL-encoded when used in URLs.
- The `as_json` parameter for the GET endpoint makes it easy to retrieve text content for editing in web interfaces.
- For large files, the raw file download (without `as_json`) is more efficient.
- When updating text files, ensure the content is valid for the file type (e.g., valid YAML for .yml files).
