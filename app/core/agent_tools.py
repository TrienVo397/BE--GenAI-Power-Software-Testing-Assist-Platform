# filepath: app/core/agent_tools.py
"""
Agent tool wrappers for background task execution.
Provides async versions of MCP tools to prevent server blocking.
"""

import logging
from typing import Dict, Any, Optional, Callable
from app.core.tasks import task_manager, TaskTypes

logger = logging.getLogger(__name__)

# List of MCP tools that should run in background to avoid server blocking
BACKGROUND_MCP_TOOLS = {
    "generate_test_cases_from_rtm": TaskTypes.GENERATE_TEST_CASES,
    "generate_rtm_from_requirements": TaskTypes.GENERATE_RTM,
    "generate_requirements_from_doc": TaskTypes.FILE_PROCESSING,
    "requirement_info_from_description": TaskTypes.FILE_PROCESSING,
    "change_requirement_info": TaskTypes.FILE_PROCESSING
}

class AgentToolWrapper:
    """Wrapper for agent tools to support background execution"""
    
    def __init__(self):
        self.long_running_tools = BACKGROUND_MCP_TOOLS.keys()
    
    def should_run_in_background(self, tool_name: str) -> bool:
        """Check if a tool should run in background to prevent blocking"""
        return tool_name in self.long_running_tools
    
    def create_background_task_for_tool(
        self, 
        tool_name: str,
        user_id: str,
        project_id: str,
        tool_func: Callable,
        **kwargs
    ) -> str:
        """Create a background task for a tool execution"""
        
        task_type = BACKGROUND_MCP_TOOLS.get(tool_name, TaskTypes.FILE_PROCESSING)
        
        task_id = task_manager.create_task(
            task_func=tool_func,
            user_id=user_id,
            task_type=task_type,
            project_id=project_id,
            **kwargs
        )
        
        logger.info(f"Created background task {task_id} for tool {tool_name}")
        return task_id
    
    def get_tool_task_message(self, tool_name: str, task_id: str) -> str:
        """Get a user-friendly message about the background task"""
        return (
            f"🔄 Started background task for {tool_name}.\n"
            f"Task ID: `{task_id}`\n\n"
            f"You can check the progress using:\n"
            f"- `/tasks/{task_id}` - Get current status\n"
            f"- `/tasks/` - List all your tasks\n\n"
            f"I'll continue processing your request while the task runs in the background."
        )

# Global instance
agent_tool_wrapper = AgentToolWrapper()
