import os
import asyncio
import glob
from typing import TypedDict, Annotated, List, Dict, Any, AsyncGenerator, Optional, Union
import uuid
from dotenv import load_dotenv

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_core.tools import tool, InjectedToolCallId

from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

# Load main system prompt
def load_main_system_prompt() -> str:
    """Load the main system prompt from file"""
    try:
        with open("ai/researchExample/Prompts/main_system_prompt.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Main system prompt file not found, using default")
        return "You are a helpful QA testing assistant working throughout the Software Development Life Cycle."

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages] # List of messages in the conversation
    project_id: uuid.UUID # Unique identifier for the project 
    current_version: str # Current version of the project (e.g., 'v1.0', 'v2.0')
    project_context: str # Context or summary of the project
    data: Optional[Dict[str, Any]] # Additional data field when needed
    

@tool
def generate_requirements_from_document_pdf_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Extracts requirements from a project SRS PDF document and generates Markdown files.

    **Inputs:**
    - `state["project_id"]` (UUID): The project identifier to locate the correct project folder
    - `state["current_version"]` (str): The version folder name (e.g., 'v0', 'v1.0', 'v2.0') containing the PDF
    - Uses 'srs.pdf' as the default filename
    
    **Behavior:**
    - Constructs the path to the PDF file using: data/project-{project_id}/versions/{current_version}/srs.pdf
    - Validates that the PDF file exists at the constructed path
    - Uses AI to analyze the PDF document and extract comprehensive requirements
    - Generates a structured requirements document in Markdown format
    - Saves requirement.md to the project's artifacts/ folder
    - Saves requirement_context.md to the project's context/ folder

    **Outputs:**
    - Updates `state["context"]` with the extracted summary content
    - Updates `state["requirements"]` with the generated Markdown requirements document
    - Updates `state["requirements_file_path"]` with the path to the generated requirement.md file
    - Updates `state["context_file_path"]` with the path to the generated context file
    - Adds a success tool message in `state["messages"]`

    **User Interaction:**
    - Don't mention the internal file paths. Always refer to the document by its filename and version only.
    - The tool automatically handles all file management and path construction.
    """
    import glob
    import sys
    import os
    from datetime import datetime
    
    logger.debug("Starting generate_requirements_from_document_pdf_tool")
    # Add the project root to the path to ensure imports work
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    try:
        from ai.mcp.gen_requierments import generate_requirements_from_doc
    except ImportError as e:
        logger.error(f"Failed to import generate_requirements_from_doc: {e}")
        return Command(update={
            "messages": [
                ToolMessage(
                    "Error: Requirements generation module not available",
                    tool_call_id=tool_call_id
                )
            ]
        })
    
    project_id = state.get('project_id')
    current_version = state.get('current_version')
    filename = 'srs.pdf'  # Default filename for SRS documents
    
    if not project_id:
        logger.error("Project ID missing from state")
        return Command(update={
            "messages": [
                ToolMessage(
                    "Error: Project ID is required to locate the document",
                    tool_call_id=tool_call_id
                )
            ]
        })
    
    if not current_version:
        logger.error("Current version missing from state")
        return Command(update={
            "messages": [
                ToolMessage(
                    "Error: Current version is required to locate the document",
                    tool_call_id=tool_call_id
                )
            ]
        })
    
    # Construct project-specific paths
    base_path = f"data/project-{project_id}"
    document_path = f"{base_path}/versions/{current_version}/{filename}"
    
    # Path to default prompts (can be made project-specific in the future)
    prompts_base = "data/default/prompts/gen_requirements"
    prompt_paths = {
        "init_1": f"{prompts_base}/initial_prompt_1.txt",
        "init_2": f"{prompts_base}/initial_prompt_2.txt", 
        "reflection": f"{prompts_base}/reflection_and_rewrite_prompt.txt",
        "summary": f"{prompts_base}/context_summary.txt"
    }
    
    logger.info(f"Looking for PDF document at: {document_path}")
    
    # Check if the PDF file exists
    if not os.path.exists(document_path):
        # Try to find any PDF files in the version folder as fallback
        version_folder = f"{base_path}/versions/{current_version}"
        pdf_pattern = f"{version_folder}/*.pdf"
        pdf_files = glob.glob(pdf_pattern)
        
        if pdf_files:
            document_path = pdf_files[0]  # Use the first PDF found
            actual_filename = os.path.basename(document_path)
            logger.info(f"PDF file '{filename}' not found, using '{actual_filename}' instead")
        else:
            logger.error(f"No PDF files found in {version_folder}")
            return Command(update={
                "messages": [
                    ToolMessage(
                        f"Error: No PDF document found in version {current_version}. Please ensure the SRS document is uploaded.",
                        tool_call_id=tool_call_id
                    )
                ]
            })
    
    # Verify all prompt files exist
    missing_prompts = []
    for prompt_name, prompt_path in prompt_paths.items():
        if not os.path.exists(prompt_path):
            missing_prompts.append(f"{prompt_name}: {prompt_path}")
    
    if missing_prompts:
        logger.error(f"Missing prompt files: {missing_prompts}")
        return Command(update={
            "messages": [
                ToolMessage(
                    f"Error: Missing required prompt files: {', '.join(missing_prompts)}",
                    tool_call_id=tool_call_id
                )
            ]
        })
    
    try:
        logger.info(f"Processing PDF document: {document_path}")
        
        # Define output paths for the generated files
        requirements_md_path = f"{base_path}/artifacts/requirement.md"
        context_md_path = f"{base_path}/context/requirement_context.md"
        
        # Call the updated function with all paths including output paths
        req_file_path, context_file_path = generate_requirements_from_doc(
            path_to_document_pdf=document_path,
            path_to_initPrompt_1=prompt_paths["init_1"],
            path_to_initPrompt_2=prompt_paths["init_2"],
            path_to_reflectionArewrite_Prompt=prompt_paths["reflection"],
            path_to_summaryPrompt=prompt_paths["summary"],
            output_requirements_md_path=requirements_md_path,
            output_context_md_path=context_md_path
        )
        
        # Read the generated content for state updates
        with open(context_file_path, 'r', encoding='utf-8') as f:
            context_content = f.read()
            
        with open(req_file_path, 'r', encoding='utf-8') as f:
            requirements_content = f.read()
        
        logger.info(f"Requirements saved to: {req_file_path}")
        logger.info(f"Context saved to: {context_file_path}")
        
        return Command(update={
            "context": context_content,
            "requirements": requirements_content,  # Now contains Markdown content
            "requirements_file_path": req_file_path,
            "context_file_path": context_file_path,
            "messages": [
                ToolMessage(
                    f"Successfully generated requirements and saved to {os.path.basename(req_file_path)} (version {current_version})",
                    tool_call_id=tool_call_id
                )
            ]
        })
        
    except Exception as e:
        logger.error(f"Error generating requirements: {str(e)}")
        return Command(update={
            "messages": [
                ToolMessage(
                    f"Error processing document: {str(e)}",
                    tool_call_id=tool_call_id
                )
            ]
        })

@tool
def generate_testCases_fromRequirements_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Generates a list of test cases from provided requirements in Markdown format.

    **Inputs:**
    - `state["requirements"]` (str): A Markdown document containing structured requirements
    - `state["context"]` (str): A brief summary to provide additional context

    **Behavior:**
    - If `requirements` or `context` are missing, returns an error message
    - Processes the Markdown requirements document to generate structured test cases
    - Returns a list of test cases in `state["testCases"]`

    **Outputs:**
    - Updates `state["testCases"]` with generated test cases
    - Adds a success message to `state["messages"]`
    """
    requirements = state.get('requirements')
    context = state.get('context')
    if not requirements or not context:
        logger.warning("Requirements or context missing for test case generation.")
        return Command(update={
            "messages": [
                ToolMessage(
                    "Requirements or Context missing",
                    tool_call_id=tool_call_id
                )
            ]
        })
    logger.info("Generating test cases from requirements.")
    # testCases_list = generate_test_cases_from_requirements(requirements, context)
    testCases_list = ["Sample test case 1", "Sample test case 2"]  # Placeholder until real implementation
    return Command(update={
        "testCases": testCases_list,
        "messages": [
            ToolMessage(
                "Successfully created test cases from the requirements",
                tool_call_id=tool_call_id
            )
        ]
    })

# LLM initialization
llm = ChatDeepSeek(
    model=settings.llm.model_name,
    temperature=settings.llm.temperature,
    max_tokens=settings.llm.max_tokens,
    timeout=settings.llm.timeout,
    max_retries=settings.llm.max_retries,
    api_key=settings.llm.api_key,
)

# Create a separate non-streaming LLM for regular calls
llm_non_streaming = ChatDeepSeek(
    model=settings.llm.model_name,
    temperature=settings.llm.temperature,
    max_tokens=settings.llm.max_tokens,
    timeout=settings.llm.timeout,
    max_retries=settings.llm.max_retries,
    api_key=settings.llm.api_key,
)

tools = [generate_testCases_fromRequirements_tool, generate_requirements_from_document_pdf_tool]
llm_with_tools = llm_non_streaming.bind_tools(tools)  # Use non-streaming for tools
tools_node = ToolNode(tools)

def call_model(state: AgentState):
    logger.info("Calling LLM with current state messages.")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": response}

# Build the LangGraph state machine
builder = StateGraph(AgentState)
builder.add_node("call_model", call_model)
builder.add_node("tools", tools_node)

builder.add_edge(START, "call_model")
builder.add_conditional_edges(
    "call_model",
    tools_condition,
)
builder.add_edge("tools", "call_model")
graph = builder.compile()

# HTTP Streaming and LLM Call Functions
# All LLM interactions should go through these functions

async def stream_agent_response(
    session_id: str,
    user_message: str,
    previous_messages: List[AnyMessage],
    project_id: uuid.UUID,
    current_version: str = "v0",
    project_context: str = "",
    additional_data: Optional[Dict[str, Any]] = None,
    use_tools: bool = True
) -> AsyncGenerator[str, None]:
    """
    Stream real LLM response using the conversation agent with HTTP streaming support.
    
    Args:
        session_id: Unique session identifier (currently not used for memory)
        user_message: The user's input message
        previous_messages: List of previous messages from database (LangChain format)
        project_id: UUID of the project
        current_version: Current version of the project documents
        project_context: Context or summary of the project
        additional_data: Additional data for agent state
        use_tools: Whether to use tools (requirements/test case generation)
    
    Yields:
        str: Content deltas for streaming response
    """
    logger.info(f"Starting agent response stream for session {session_id}")
    
    try:
        # Create conversation state with provided data
        conversation_state = AgentState(
            messages=previous_messages + [HumanMessage(content=user_message)],
            project_id=project_id,
            current_version=current_version,
            project_context=project_context,
            data=additional_data or {}
        )
        
        if use_tools:
            # Use the full LangGraph agent with tools
            logger.info("Using LangGraph agent with tools")
            
            # For now, we'll use invoke and then stream the final response
            # TODO: Implement proper streaming with tool calls
            result = graph.invoke(conversation_state)
            
            # Get the final AI message content
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content') and final_message.content:
                # Stream the content word by word for better UX
                words = final_message.content.split()
                for i, word in enumerate(words):
                    if i == 0:
                        yield word
                    else:
                        yield f" {word}"
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.01)
            else:
                yield "I've completed the requested operation. Please check the generated files."
        else:
            # Use simple LLM streaming without tools
            async for chunk in stream_simple_llm_response(user_message):
                yield chunk
        
    except Exception as e:
        logger.error(f"Error in agent response stream: {str(e)}")
        yield f"I apologize, but I encountered an error while processing your request: {str(e)}"

async def stream_simple_llm_response(
    user_message: str,
    system_prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream response using simple LLM call (fallback option).
    
    Args:
        user_message: The user's input message
        system_prompt: Optional system prompt (uses default if None)
    
    Yields:
        str: Content deltas for streaming response
    """
    logger.info("Starting simple LLM response stream")
    
    try:
        # Create a simple conversation with the LLM
        messages = [
            SystemMessage(content=system_prompt or load_main_system_prompt()),
            HumanMessage(content=user_message)
        ]
        
        logger.info(f"Streaming LLM call with messages: {len(messages)} messages")
        
        # Stream response from LLM using streaming=True
        chunk_count = 0
        async for chunk in llm.astream(messages):
            chunk_count += 1
            logger.info(f"Received chunk {chunk_count}: {type(chunk)} - {hasattr(chunk, 'content')}")
            
            if hasattr(chunk, 'content') and chunk.content:
                content = str(chunk.content)
                logger.info(f"Yielding chunk content: '{content[:50]}...'")
                yield content
        
        logger.info(f"Streaming completed with {chunk_count} chunks")
                
    except Exception as e:
        logger.error(f"Error in simple LLM response stream: {str(e)}")
        yield f"I apologize, but I encountered an error while processing your request: {str(e)}"

