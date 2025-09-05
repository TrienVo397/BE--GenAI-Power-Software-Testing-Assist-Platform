# filepath: ai/agents/background_tools.py
"""
Background-aware tool implementations for the conversation agent.
Provides non-blocking versions of MCP tools that create background tasks.
"""

import logging
import os
import sys
from typing import Dict, Any
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.graph import Command
from typing_extensions import Annotated
from langgraph.types import InjectedState, InjectedToolCallId

# Add root to sys.path for imports
root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if root not in sys.path:
    sys.path.append(root)

from app.core.tasks import task_manager, TaskTypes
from ai.agents.conversation_agent import AgentState

logger = logging.getLogger(__name__)

@tool
def generate_test_cases_background_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Creates a background task to generate test cases from RTM content.
    This prevents server blocking during long-running test case generation.
    """
    try:
        project_id = state.get("project_id")
        if not project_id:
            return Command(update={
                "messages": [ToolMessage(
                    "Error: Project ID not found in conversation state", 
                    tool_call_id=tool_call_id
                )]
            })
        
        # Get RTM content from project artifacts
        project_path = f"data/project-{project_id}"
        rtm_path = os.path.join(project_path, "artifacts", "requirements_traceability_matrix.md")
        
        if not os.path.exists(rtm_path):
            return Command(update={
                "messages": [ToolMessage(
                    f"Error: RTM file not found at {rtm_path}. Please generate an RTM first.",
                    tool_call_id=tool_call_id
                )]
            })
        
        with open(rtm_path, 'r', encoding='utf-8') as f:
            rtm_content = f.read()
        
        # Get user ID from state (if available) or use a default
        user_id = state.get("user_id", "system")
        
        # Create background task
        task_id = task_manager.create_task(
            task_func=_background_generate_test_cases,
            user_id=str(user_id),
            task_type=TaskTypes.GENERATE_TEST_CASES,
            project_id=project_id,
            rtm_content=rtm_content,
            project_id_param=project_id
        )
        
        message = (
            f"🔄 **Background Task Started**\n\n"
            f"I've started generating test cases from your RTM in the background.\n\n"
            f"**Task ID:** `{task_id}`\n"
            f"**Task Type:** Test Case Generation\n"
            f"**Project:** {project_id}\n\n"
            f"You can check the progress using:\n"
            f"- `GET /api/v1/tasks/{task_id}` - Get current status\n"
            f"- `GET /api/v1/tasks/` - List all your tasks\n\n"
            f"The test cases will be saved to your project artifacts once complete. "
            f"I'll continue to assist you with other tasks while this runs in the background!"
        )
        
        return Command(update={
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)]
        })
        
    except Exception as e:
        logger.error(f"Error creating background test case generation task: {str(e)}")
        return Command(update={
            "messages": [ToolMessage(
                f"Error creating background task: {str(e)}",
                tool_call_id=tool_call_id
            )]
        })

@tool
def generate_rtm_background_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Creates a background task to generate RTM from requirements.
    This prevents server blocking during long-running RTM generation.
    """
    try:
        project_id = state.get("project_id")
        if not project_id:
            return Command(update={
                "messages": [ToolMessage(
                    "Error: Project ID not found in conversation state", 
                    tool_call_id=tool_call_id
                )]
            })
        
        # Get requirements content from project artifacts
        project_path = f"data/project-{project_id}"
        requirements_path = os.path.join(project_path, "artifacts", "requirement.md")
        
        if not os.path.exists(requirements_path):
            return Command(update={
                "messages": [ToolMessage(
                    f"Error: Requirements file not found at {requirements_path}. Please upload requirements first.",
                    tool_call_id=tool_call_id
                )]
            })
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            requirements_content = f.read()
        
        # Get user ID from state (if available) or use a default
        user_id = state.get("user_id", "system")
        
        # Create background task
        task_id = task_manager.create_task(
            task_func=_background_generate_rtm,
            user_id=str(user_id),
            task_type=TaskTypes.GENERATE_RTM,
            project_id=project_id,
            requirements_content=requirements_content,
            project_id_param=project_id
        )
        
        message = (
            f"🔄 **Background Task Started**\n\n"
            f"I've started generating the Requirements Traceability Matrix (RTM) in the background.\n\n"
            f"**Task ID:** `{task_id}`\n"
            f"**Task Type:** RTM Generation\n"
            f"**Project:** {project_id}\n\n"
            f"You can check the progress using:\n"
            f"- `GET /api/v1/tasks/{task_id}` - Get current status\n"
            f"- `GET /api/v1/tasks/` - List all your tasks\n\n"
            f"The RTM will be saved to your project artifacts once complete. "
            f"Feel free to continue our conversation while this processes!"
        )
        
        return Command(update={
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)]
        })
        
    except Exception as e:
        logger.error(f"Error creating background RTM generation task: {str(e)}")
        return Command(update={
            "messages": [ToolMessage(
                f"Error creating background task: {str(e)}",
                tool_call_id=tool_call_id
            )]
        })

# Background task execution functions
def _background_generate_test_cases(rtm_content: str, project_id_param: str):
    """Execute test case generation in background task"""
    try:
        logger.info(f"Starting background test case generation for project {project_id_param}")
        
        # Import and use the existing MCP tool
        from ai.mcp.gen_testCases import generate_test_cases_from_rtm
        
        # Set up paths for prompts
        prompts_base = "data/default/prompts/gen_testCases"
        prompt_paths = {
            "init_1": os.path.join(prompts_base, "initPrompt_1.txt"),
            "init_2": os.path.join(prompts_base, "initPrompt_2.txt"),
            "reflection": os.path.join(prompts_base, "reflectionPrompt.txt"),
            "final": os.path.join(prompts_base, "finalPrompt.txt")
        }
        
        # Output path
        out_path = f"data/project-{project_id_param}/artifacts"
        os.makedirs(out_path, exist_ok=True)
        
        # Generate test cases
        result_path = generate_test_cases_from_rtm(
            rtm_content=rtm_content,
            path_to_initPrompt_1=prompt_paths["init_1"],
            path_to_initPrompt_2=prompt_paths["init_2"],
            path_to_reflectionPrompt=prompt_paths["reflection"],
            path_to_finalPrompt=prompt_paths["final"],
            out_path=out_path
        )
        
        logger.info(f"Test case generation completed for project {project_id_param}")
        
        return {
            "project_id": project_id_param,
            "generated_file": result_path,
            "rtm_content_length": len(rtm_content),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in background test case generation: {str(e)}")
        raise

def _background_generate_rtm(requirements_content: str, project_id_param: str):
    """Execute RTM generation in background task"""
    try:
        logger.info(f"Starting background RTM generation for project {project_id_param}")
        
        # Import and use the existing MCP tool
        from ai.mcp.gen_rtm import generate_rtm_from_requirements
        
        # Set up paths for prompts
        prompts_base = "data/default/prompts/gen_rtm"
        prompt_paths = {
            "init": os.path.join(prompts_base, "initPrompt.txt"),
            "reflection": os.path.join(prompts_base, "reflectionPrompt.txt"),
            "final": os.path.join(prompts_base, "finalPrompt.txt")
        }
        
        # Output path
        out_path = f"data/project-{project_id_param}/artifacts"
        os.makedirs(out_path, exist_ok=True)
        
        # Generate RTM
        result_path = generate_rtm_from_requirements(
            requirements_content=requirements_content,
            path_to_initPrompt=prompt_paths["init"],
            path_to_reflectionPrompt=prompt_paths["reflection"],
            path_to_finalPrompt=prompt_paths["final"],
            out_path=out_path
        )
        
        logger.info(f"RTM generation completed for project {project_id_param}")
        
        return {
            "project_id": project_id_param,
            "generated_file": result_path,
            "requirements_content_length": len(requirements_content),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in background RTM generation: {str(e)}")
        raise

# List of background tools
background_tools = [
    generate_test_cases_background_tool,
    generate_rtm_background_tool
]
