import os
import asyncio
import glob
from typing import TypedDict, Annotated, List, Dict, Any, AsyncGenerator, Optional, Union
import uuid
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_core.tools import tool, InjectedToolCallId

from app.core.config import settings

import logging

logger = logging.getLogger(__name__)
load_dotenv()
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

    **Behavior:**
    - Uses AI to analyze the PDF document and extract comprehensive requirements
    - Generates a structured requirements document in Markdown format

    **Outputs:**
    - Adds a success tool message in `state["messages"]`
    - A new requirement.md in project's artifacts/ folder
    - A new requirement_context.md in project's context/ folder

    **User Interaction:**
    - Don't mention the internal file paths. Always refer to the document by its filename and version only.

    **Note**
    - The file will be name "SRS.pdf" do not mention about it, if no "SRS.pdf" file found, use the file name that most sensible.
    """
    import os, sys, glob

    logger.info("Starting requirements extraction from document...")
    
    project_id = state.get("project_id")
    version = state.get("current_version")
    if not project_id or not version:
        msg = "Missing project ID" if not project_id else "Missing version"
        return Command(update={"messages": [ToolMessage(f"Error: {msg}.", tool_call_id=tool_call_id)]})

    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if root not in sys.path: sys.path.append(root)
    try:
        from ai.mcp.gen_requirements import generate_requirements_from_doc
    except ImportError:
        return Command(update={"messages": [ToolMessage("Error: Requirements module not available.", tool_call_id=tool_call_id)]})

    base = f"data/project-{project_id}"
    doc_path = f"{base}/versions/{version}/srs.pdf"
    if not os.path.exists(doc_path):
        pdfs = glob.glob(f"{base}/versions/{version}/*.pdf")
        if not pdfs:
            return Command(update={"messages": [ToolMessage(f"Error: No PDF found in version {version}.", tool_call_id=tool_call_id)]})
        doc_path = pdfs[0]

    prompts = {
        "init_1": "data/default/prompts/gen_requirements/initial_prompt_1.txt",
        "init_2": "data/default/prompts/gen_requirements/initial_prompt_2.txt",
        "reflection": "data/default/prompts/gen_requirements/reflection_and_rewrite_prompt.txt",
        "summary": "data/default/prompts/gen_requirements/context_summary.txt"
    }
    missing = [name for name, path in prompts.items() if not os.path.exists(path)]
    if missing:
        return Command(update={"messages": [ToolMessage(f"Error: Missing prompt files: {', '.join(missing)}", tool_call_id=tool_call_id)]})

    try:
        req_path = f"{base}/artifacts/requirement.md"
        ctx_path = f"{base}/context/requirement_context.md"
        req_path, ctx_path = generate_requirements_from_doc(
            path_to_document_pdf=doc_path,
            path_to_initPrompt_1=prompts["init_1"],
            path_to_initPrompt_2=prompts["init_2"],
            path_to_reflectionArewrite_Prompt=prompts["reflection"],
            path_to_summaryPrompt=prompts["summary"],
            output_requirements_md_path=req_path,
            output_context_md_path=ctx_path
        )
        return Command(update={"messages": [ToolMessage(f"Requirements saved to {os.path.basename(req_path)} (version {version})", tool_call_id=tool_call_id)]})
    except Exception as e:
        return Command(update={"messages": [ToolMessage(f"Error processing document: {e}", tool_call_id=tool_call_id)]})

@tool
def generate_testCases_from_RTM_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Generates test cases from the Requirements Traceability Matrix (RTM).

    **Behavior:**
    - Reads the RTM from the project's artifacts folder
    - Extracts test case IDs and descriptions
    - Generates detailed test cases in Markdown format
    - Saves the test cases to a file in the project's artifacts folder

    **Outputs:**
    - Updates `state["testCases"]` with generated test cases
    - Adds a success message to `state["messages"]`
    """
    import os, sys
    
    logger.info("Starting test case generation from RTM...")
    
    project_id = state.get("project_id")
    if not project_id:
        return Command(update={"messages": [ToolMessage("Error: Missing project ID.", tool_call_id=tool_call_id)]})

    base = f"data/project-{project_id}/artifacts"
    rtm_path = f"{base}/requirements_traceability_matrix.md"
    out_path = f"{base}/test_cases.md"
    prompts_base = "data/default/prompts/gen_testCases"
    prompt_paths = {
        "init_1": f"{prompts_base}/initial_prompt_1.txt",
        "init_2": f"{prompts_base}/initial_prompt_2.txt", 
        "reflection": f"{prompts_base}/reflection_prompt.txt",
        "final": f"{prompts_base}/final_prompt.txt"
    }
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
    if not os.path.exists(rtm_path):
        return Command(update={"messages": [ToolMessage("Error: RTM file not found. Please generate it first.", tool_call_id=tool_call_id)]})

    try:
        with open(rtm_path, 'r', encoding='utf-8') as f:
            rtm_content = f.read()

        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if root not in sys.path: sys.path.append(root)

        from ai.mcp.gen_testCases import generate_test_cases_from_rtm
        out_path = generate_test_cases_from_rtm( rtm_content = rtm_content,
            path_to_initPrompt_1=prompt_paths["init_1"],
            path_to_initPrompt_2=prompt_paths["init_2"],
            path_to_reflectionPrompt=prompt_paths["reflection"],
            path_to_finalPrompt=prompt_paths["final"],
            out_path=out_path)


        return Command(update={
            "messages": [ToolMessage(f"Test cases generated successfully. Saved to {os.path.basename(out_path)}", tool_call_id=tool_call_id)]
        })

    except Exception as e:
        return Command(update={"messages": [ToolMessage(f"Error: {e}", tool_call_id=tool_call_id)]})

@tool
def generate_rtm_fromRequirements_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Generates a Requirements Traceability Matrix (RTM) from provided requirements in Markdown format.
    To create a comprehensive mapping between requirements and test cases to ensure complete test coverage.

    **Behavior:**
    - Reads the requirements and context from their respective files
    - Analyzes requirements and maps them to test cases with IDs and descriptions
    
    **Outputs:**
    - A Markdown file as RTM to the project's artifacts/ folder
    - Adds a success tool message in `state["messages"]`

    **User Interaction:**
    - Don't mention the internal file paths. Always refer to the RTM by its filename only.
    - Emphasize that this creates requirement-to-test-case mapping for full traceability.
    """
    import os, sys

    logger.info("Starting RTM generation from requirements...")
    
    project_id = state.get("project_id")
    if not project_id:
        return Command(update={"messages": [ToolMessage("Error: Missing project ID.", tool_call_id=tool_call_id)]})

    base = f"data/project-{project_id}"
    req_path = f"{base}/artifacts/requirement.md"
    ctx_path = f"{base}/context/requirement_context.md"
    rtm_path = f"{base}/artifacts/requirements_traceability_matrix.md"
    prompt_path = "data/default/prompts/gen_rtm/rtm_generation_prompt.txt"

    for path, label in [(req_path, "Requirements"), (ctx_path, "Context"), (prompt_path, "Prompt")]:
        if not os.path.exists(path):
            return Command(update={"messages": [ToolMessage(f"Error: {label} file not found.", tool_call_id=tool_call_id)]})

    try:
        with open(req_path, 'r', encoding='utf-8') as f: req = f.read()
        with open(ctx_path, 'r', encoding='utf-8') as f: ctx = f.read()

        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if root not in sys.path: sys.path.append(root)

        from ai.mcp.gen_rtm import generate_rtm_from_requirements
        rtm_content = generate_rtm_from_requirements(req, ctx, prompt_path, rtm_path)

        return Command(update={
            "messages": [ToolMessage(f"RTM generated successfully. Saved to {os.path.basename(rtm_path)}", tool_call_id=tool_call_id)]
        })

    except Exception as e:
        return Command(update={"messages": [ToolMessage(f"Error: {e}", tool_call_id=tool_call_id)]})

@tool
def get_requirement_info_by_lookup_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    target_key: Annotated[str, 'The column name to look up in the Markdown table'],
    target_value: Annotated[str, 'The value to match in the Markdown table']
) -> Command:
    """
    Inquiry the requirements that match with the target key-value and get the full information of those requirements (ID, description, priority, dependency)

    **Behavior**
    - Parses the Markdown requirements file and finds rows where the target column matches the target value.
    - Returns a list of dictionaries for all matching requirements.

    **Outputs:**
    - Adds a Tool message to `state["messages"]`. If successful, the tool message is a list containing dictionaries of the aligned requirements, else the message is an empty list.

    **Note**
    - The Markdown table must have headers matching the column names.
    - The function is case-insensitive for keys and values.
    """
    import os
    import re

    project_id = state.get("project_id")
    if not project_id:
        return Command(update={"messages": [ToolMessage("Error: Missing project ID.", tool_call_id=tool_call_id)]})

    req_path = f"data/project-{project_id}/artifacts/requirement.md"
    if not os.path.exists(req_path):
        return Command(update={"messages": [ToolMessage("Requirements file not found.", tool_call_id=tool_call_id)]})

    with open(req_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Extract Markdown table
    table_match = re.search(r"\|.*?\|\n\|[-| ]+\|\n((?:\|.*\|\n?)+)", md_text, re.DOTALL)
    if not table_match:
        return Command(update={"messages": [ToolMessage("No requirements table found.", tool_call_id=tool_call_id)]})

    table = table_match.group(0).strip().split('\n')
    headers = [h.strip() for h in table[0].split('|')[1:-1]]
    results = []
    
    # Find the target column index
    target_col_index = None
    for i, header in enumerate(headers):
        if header.lower() == target_key.lower():
            target_col_index = i
            break
    
    if target_col_index is None:
        return Command(update={"messages": [ToolMessage(f"Column '{target_key}' not found in requirements table.", tool_call_id=tool_call_id)]})
    
    for row in table[2:]:  # skip header and separator
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) == len(headers):
            # Check only the target column for the match
            if target_col_index < len(cols) and str(cols[target_col_index]).lower() == str(target_value).lower():
                req_dict = dict(zip(headers, cols))
                results.append(req_dict)
    
    return Command(update={"messages": [ToolMessage(content=str(results), tool_call_id=tool_call_id)]})

# ...existing code...

@tool
def get_requirement_info_from_description_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    description: Annotated[str, "The description that the tool uses to find full information"]
) -> Command:
    """
    Inquiry requirements that meet the description and get the full information of those requirements (ID, description, priority, dependency).

    **Behavior:**
    - Reads requirements from the project's requirements Markdown file.
    - Uses an LLM to parse and find requirements that align with the given description.

    **Outputs:**
    - Adds a Tool message to `state["messages"]`. If successful, the tool message is a list containing dictionaries of the aligned requirements, else the message is an empty list.

    **Note**
    - This tool uses LLM to locate the requirement, thus, resource intensive. If it is possible to locate the requirement without natural language processing, use the other way or tool.
    """
    import os
    import sys

    project_id = state.get("project_id")
    if not project_id:
        return Command(update={"messages": [ToolMessage(content="Error: Missing project ID.", tool_call_id=tool_call_id)]})

    req_path = f"data/project-{project_id}/artifacts/requirement.md"
    if not os.path.exists(req_path):
        return Command(update={"messages": [ToolMessage(content="Requirements file not found.", tool_call_id=tool_call_id)]})

    # Add ai/mcp to sys.path for import
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if root not in sys.path:
        sys.path.append(root)
    try:
        from ai.mcp.requirement_info_from_description import requirement_info_from_description
    except ImportError:
        return Command(update={"messages": [ToolMessage(content="Error: Requirement info module not available.", tool_call_id=tool_call_id)]})

    try:
        tool_answer_string = requirement_info_from_description(description, req_path)
        return Command(update={"messages": [ToolMessage(content=tool_answer_string, tool_call_id=tool_call_id)]})
    except Exception as e:
        return Command(update={"messages": [ToolMessage(content=f"Error: {e}", tool_call_id=tool_call_id)]})


# ...existing code...

@tool
def change_requirement_info_tool(
    state: Annotated[AgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    req_id: Annotated[str, "The ID of the requirement that needs change. The tool uses this to find the targeted requirement"],
    attribute: Annotated[str, 'The attribute inside the requirement dictionary that needs change. Must be a valid column name'],
    value: Annotated[str, 'The value that the attribute of the requirement will change into']
) -> Command:
    """
    Change the information of a requirement (i.e., update one attribute value in the Markdown requirements table).

    **Behavior**
    - Finds the requirement row by ID in the Markdown file.
    - Updates the specified attribute (column) with the new value.
    - If the requirement or attribute does not exist, returns an error ToolMessage.

    **Output**
    - Updates the requirements Markdown file in-place.
    - Adds a success ToolMessage.

    **Note**
    - The requirements file must exist.
    - Use other tools to locate the requirement ID if needed.
    """
    import os
    import sys

    project_id = state.get("project_id")
    if not project_id:
        return Command(update={"messages": [ToolMessage(content="Error: Missing project ID.", tool_call_id=tool_call_id)]})

    req_path = f"data/project-{project_id}/artifacts/requirement.md"
    if not os.path.exists(req_path):
        return Command(update={"messages": [ToolMessage(content="Requirements file not found.", tool_call_id=tool_call_id)]})

    # Add ai/mcp to sys.path for import
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if root not in sys.path:
        sys.path.append(root)
    try:
        from ai.mcp.change_requirement_info import change_requirement_info
    except ImportError:
        return Command(update={"messages": [ToolMessage(content="Error: Change requirement module not available.", tool_call_id=tool_call_id)]})

    try:
        result, msg = change_requirement_info(req_path, req_id, attribute, value)
        if result:
            return Command(update={"messages": [ToolMessage(content="Successfully modified the requirement.", tool_call_id=tool_call_id)]})
        else:
            return Command(update={"messages": [ToolMessage(content=msg, tool_call_id=tool_call_id)]})
    except Exception as e:
        return Command(update={"messages": [ToolMessage(content=f"Error: {e}", tool_call_id=tool_call_id)]})

# ...existing code...

# ...existing code...
# LLM initialization
# llm = ChatDeepSeek(
#     model=settings.llm.model_name,
#     temperature=settings.llm.temperature,
#     max_tokens=settings.llm.max_tokens,
#     timeout=settings.llm.timeout,
#     max_retries=settings.llm.max_retries,
#     api_key=settings.llm.api_key,
# )
google_llm_api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    max_tokens = None,
    api_key = google_llm_api_key,
)

# Create a separate non-streaming LLM for regular calls
# llm_non_streaming = ChatDeepSeek(
#     model=settings.llm.model_name,
#     temperature=settings.llm.temperature,
#     max_tokens=settings.llm.max_tokens,
#     timeout=settings.llm.timeout,
#     max_retries=settings.llm.max_retries,
#     api_key=settings.llm.api_key,
# )

llm_non_streaming = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    max_tokens = None,
    api_key = "AIzaSyB3F2BGLaXhgxn4p0wuB1fPKycapCxk2no",
)

tools = [generate_testCases_from_RTM_tool, generate_requirements_from_document_pdf_tool, generate_rtm_fromRequirements_tool, get_requirement_info_by_lookup_tool,
         get_requirement_info_from_description_tool,change_requirement_info_tool]
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
            
            logger.info(f"Conversation state: {conversation_state}")
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

