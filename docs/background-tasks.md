# Background Task System Documentation

## Overview

The background task system prevents server blocking during long-running operations like test case generation and coverage analysis. This is essential for multi-user environments where one user's heavy operation shouldn't block other users.

**Note:** As of September 2025, tasks are handled internally by the bot system and conversation agent. The task API endpoints have been removed from the user-facing API, as tasks are automatically managed during chat interactions and bot operations.

## Problem Solved

**Before:** MCP tools like `generate_test_cases_from_rtm` would run synchronously, blocking the entire FastAPI server until completion. This could take minutes for large documents, making the system unusable for other users.

**After:** Long-running operations are executed as background tasks through the bot endpoints and conversation agent, returning immediately with responses while processing continues in the background.

## Architecture

### Components

1. **TaskManager** (`app/core/tasks.py`)
   - Manages task lifecycle (pending → running → completed/failed)
   - Stores task metadata and results in memory
   - Provides task status tracking and cancellation
   - Automatic cleanup of old completed tasks

2. **Task API** (`app/api/v1/endpoints/tasks.py`)
   - RESTful endpoints for task management
   - User-scoped task access (users can only see their own tasks)
   - Endpoints for creating, monitoring, and cancelling tasks

3. **Background Tools** (`ai/agents/background_tools.py`)
   - Non-blocking versions of MCP tools
   - Integration with conversation agent
   - User-friendly progress messages

4. **Updated Endpoints**
   - `bot.py` - Coverage analysis now returns task ID instead of blocking
   - `tasks.py` - New task management endpoints

## API Usage

### Creating Background Tasks

#### Test Case Generation
```http
POST /api/v1/tasks/generate-test-cases
Content-Type: application/json

{
    "rtm_content": "REQ-001: User shall be able to login...",
    "project_id": "123e4567-e89b-12d3-a456-426614174000",
    "generation_options": {
        "include_negative_tests": true,
        "test_framework": "pytest"
    }
}
```

#### Coverage Analysis
```http
POST /api/v1/bot/coverage-test
Content-Type: application/json

{
    "project_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Both return a `TaskResponse` with the task ID for tracking.

### Monitoring Tasks

#### Get Specific Task Status
```http
GET /api/v1/tasks/{task_id}
```

#### List All User Tasks
```http
GET /api/v1/tasks/
```

#### Filter Tasks by Type
```http
GET /api/v1/tasks/?task_type=generate_test_cases
```

### Task Lifecycle

1. **Created** - Task is queued but not started
2. **Running** - Task is actively executing  
3. **Completed** - Task finished successfully with results
4. **Failed** - Task encountered an error
5. **Cancelled** - Task was manually cancelled

### Response Format

```json
{
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user123",
    "project_id": "proj456", 
    "task_type": "generate_test_cases",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "started_at": "2024-01-15T10:30:05Z",
    "completed_at": "2024-01-15T10:35:00Z",
    "result": {
        "generated_files": ["test_case_1.py", "test_case_2.py"],
        "total_count": 15
    },
    "error": null,
    "progress": {
        "current_step": "completed",
        "total_steps": 3,
        "percentage": 100
    }
}
```

## Conversation Agent Integration

The conversation agent now includes background-aware tools that:

1. Detect when a tool should run in background
2. Create appropriate background tasks
3. Return user-friendly messages with task IDs
4. Allow users to continue conversations while tasks run

### Example Agent Response

```
🔄 Background Task Started

I've started generating test cases from your RTM in the background.

Task ID: `abc123-def456-ghi789`
Task Type: Test Case Generation
Project: my-project-123

You can check the progress using:
- GET /api/v1/tasks/abc123-def456-ghi789 - Get current status
- GET /api/v1/tasks/ - List all your tasks

The test cases will be saved to your project artifacts once complete. 
I'll continue to assist you with other tasks while this runs in the background!
```

## Migration from Synchronous Operations

### Bot Endpoint Changes

The bot coverage analysis endpoint now:
- **New**: `POST /bot/coverage-test` - Returns task ID immediately
- **Deprecated**: `POST /bot/coverage-test-sync` - Still available but marked deprecated

### Conversation Agent Changes

Original blocking tools like `generate_testCases_from_rtm_tool` are supplemented with:
- `generate_test_cases_background_tool` - Creates background task
- `generate_rtm_background_tool` - Creates background RTM generation task

## Configuration

### Task Types
- `GENERATE_TEST_CASES` - Test case generation from RTM
- `COVERAGE_ANALYSIS` - Coverage analysis and reporting
- `GENERATE_RTM` - RTM generation from requirements  
- `FILE_PROCESSING` - General file processing tasks

### Cleanup
- Completed/failed tasks are automatically cleaned up after 24 hours
- Running tasks can be cancelled by users
- Task storage is currently in-memory (consider Redis for production)

## Benefits

1. **Non-blocking Operations** - Server remains responsive during long tasks
2. **Multi-user Support** - Users don't interfere with each other's operations
3. **Progress Tracking** - Users can monitor task status and progress
4. **Error Isolation** - Task failures don't crash the server
5. **Cancellation Support** - Users can cancel long-running tasks
6. **Resource Management** - Automatic cleanup prevents memory leaks

## Future Enhancements

1. **Persistent Storage** - Use Redis or database for task storage
2. **Real-time Updates** - WebSocket notifications for task status changes
3. **Task Queuing** - Proper job queue with priority and retry logic
4. **Resource Limits** - Per-user concurrent task limits
5. **Progress Reporting** - More granular progress updates during execution
6. **Task Dependencies** - Support for chained/dependent tasks

## Usage Examples

### Frontend Integration

```javascript
// Create a task
const response = await fetch('/api/v1/tasks/generate-test-cases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        rtm_content: rtmText,
        project_id: projectId
    })
});

const task = await response.json();
const taskId = task.task_id;

// Poll for completion
const pollTask = async () => {
    const statusResponse = await fetch(`/api/v1/tasks/${taskId}`);
    const taskStatus = await statusResponse.json();
    
    if (taskStatus.status === 'completed') {
        console.log('Task completed!', taskStatus.result);
    } else if (taskStatus.status === 'failed') {
        console.error('Task failed:', taskStatus.error);
    } else {
        // Still running, poll again
        setTimeout(pollTask, 2000);
    }
};

pollTask();
```

This system ensures the platform can scale to support multiple concurrent users without performance degradation from long-running AI operations.
