# filepath: app/core/tasks.py
"""
Background task management system for long-running operations.
Prevents server blocking during MCP tool execution and other CPU-intensive tasks.
"""

import asyncio
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from enum import Enum
import logging
import traceback
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    """Information about a background task"""
    task_id: str
    user_id: str
    project_id: Optional[str]
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    progress: Optional[Dict[str, Any]]
    
class TaskManager:
    """Manages background tasks for the application"""
    
    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._running_tasks: Dict[str, Optional[asyncio.Task]] = {}
        
    def create_task(
        self, 
        task_func: Callable,
        user_id: str,
        task_type: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create and start a new background task"""
        
        task_id = str(uuid.uuid4())
        
        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
            result=None,
            error=None,
            progress=None
        )
        
        self._tasks[task_id] = task_info
        
        # Check if we have an event loop first, then create task accordingly
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we get here, we have an event loop, so use ensure_future
            async_task = asyncio.ensure_future(self._run_task(task_id, task_func, **kwargs))
            self._running_tasks[task_id] = async_task
        except RuntimeError:
            # No event loop is running, use thread-based execution
            import threading
            
            def run_in_background():
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._run_task(task_id, task_func, **kwargs))
                finally:
                    loop.close()
            
            # Run in a separate thread
            thread = threading.Thread(target=run_in_background, daemon=True)
            thread.start()
            # Don't store task reference for thread-based execution
        
        logger.info(f"Created background task {task_id} of type {task_type} for user {user_id}")
        
        return task_id
        
    async def _run_task(self, task_id: str, task_func: Callable, **kwargs):
        """Execute a task in the background"""
        
        task_info = self._tasks[task_id]
        
        try:
            # Update status to running
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.now(timezone.utc)
            
            logger.info(f"Starting execution of task {task_id}")
            
            # Execute the task function
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(**kwargs)
            else:
                # Run sync function in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: task_func(**kwargs))
            
            # Task completed successfully
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now(timezone.utc)
            task_info.result = result
            
            logger.info(f"Task {task_id} completed successfully")
            
        except asyncio.CancelledError:
            # Task was cancelled
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now(timezone.utc)
            logger.info(f"Task {task_id} was cancelled")
            
        except Exception as e:
            # Task failed
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.now(timezone.utc)
            task_info.error = str(e)
            
            logger.error(f"Task {task_id} failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        finally:
            # Clean up the running task reference
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """Get the current status of a task"""
        return self._tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if task is not None:
                task.cancel()
                logger.info(f"Cancelled task {task_id}")
                return True
        return False
    
    def get_user_tasks(self, user_id: str, task_type: Optional[str] = None) -> list[TaskInfo]:
        """Get all tasks for a specific user, optionally filtered by type"""
        user_tasks = [
            task for task in self._tasks.values() 
            if task.user_id == user_id
        ]
        
        if task_type:
            user_tasks = [task for task in user_tasks if task.task_type == task_type]
            
        return sorted(user_tasks, key=lambda x: x.created_at, reverse=True)
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks"""
        current_time = datetime.now(timezone.utc)
        tasks_to_remove = []
        
        for task_id, task_info in self._tasks.items():
            if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task_info.completed_at and
                (current_time - task_info.completed_at).total_seconds() > max_age_hours * 3600):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self._tasks[task_id]
            logger.info(f"Cleaned up old task {task_id}")
    
    def update_task_progress(self, task_id: str, progress: Dict[str, Any]):
        """Update the progress of a running task"""
        if task_id in self._tasks:
            self._tasks[task_id].progress = progress
            logger.debug(f"Updated progress for task {task_id}: {progress}")

# Global task manager instance
task_manager = TaskManager()

# Task type constants
class TaskTypes:
    GENERATE_TEST_CASES = "generate_test_cases"
    COVERAGE_ANALYSIS = "coverage_analysis"
    GENERATE_RTM = "generate_rtm"
    FILE_PROCESSING = "file_processing"
