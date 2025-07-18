import os
import asyncio
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
    project_context: str # Context or summary of the project
    data: Optional[Dict[str, Any]] # Additional data field when needed
    

@tool
def generate_requirements_from_document_pdf_tool(
    x: Annotated[str, "the PATH to the pdf document from which the tool will generate requirements"],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Extracts a brief summary and a list of requirements from a project document.

    **Inputs:**
    - `x` (str): The PATH to the pdf document
    
    **Behavior:**
    - Decodes the PDF document from input path into base64 string.
    - Analyzes the document content to extract project requirements.
    - Generates a summary of the document.

    **Outputs:**
    - Updates `state["context"]` with the extracted summary.
    - Updates `state["requirements"]` with a structured list of requirements.
    - Adds a success tool message in `state["messages"]`.

    **User Interaction**
    - Don't mention anything about the path of the pdf. Always mention ONLY about the pdf itself.
    """
    logger.info("Generating requirements from document: %s", x)
    # requirements, context = generate_requirements_from_doc(x)
    requirements, context = [{"id": 1, "requirement": "Example requirement 1"},
        {"id": 2, "requirement": "Example requirement 2"}
    ], "This is a brief summary of the document."
    
    return Command(update={
        "context": context,
        "requirements": requirements,
        "messages": [
            ToolMessage(
                "Successfully created requirements from the document",
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
    Generates a list of test cases from provided requirements.

    **Inputs:**
    - `state["requirements"]` (list[dict]): A list of software or system requirements.
    - `state["context"]` (str): A brief summary to provide additional context.

    **Behavior:**
    - If `requirements` or `context` are missing, returns an error message.
    - Processes requirements to generate structured test cases.
    - Returns a list of test cases in `state["testCases"]`.

    **Outputs:**
    - Updates `state["testCases"]` with generated test cases.
    - Adds a success message to `state["messages"]`.
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
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# HTTP Streaming and LLM Call Functions
# All LLM interactions should go through these functions

async def stream_agent_response(
    session_id: str,
    user_message: str,
    previous_messages: List[AnyMessage],
    project_id: uuid.UUID,
    project_context: str = "",
    additional_data: Optional[Dict[str, Any]] = None,
    use_tools: bool = True
) -> AsyncGenerator[str, None]:
    """
    Stream real LLM response using the conversation agent with HTTP streaming support.
    
    Args:
        session_id: Unique session identifier for memory persistence
        user_message: The user's input message
        previous_messages: List of previous messages from database (LangChain format)
        project_id: UUID of the project
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
            project_context=project_context,
            data=additional_data or {}
        )
        
        # Stream the response using direct LLM streaming for better real-time performance
        config = {"configurable": {"thread_id": session_id}}
        
        if use_tools:
            # Using simple LLM streaming for better real-time performance
            # Tool streaming can be added later if needed
            logger.info("Using simple LLM streaming for better real-time performance")
            async for chunk in stream_simple_llm_response(user_message):
                yield chunk
        else:
            # Use simple LLM streaming
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

