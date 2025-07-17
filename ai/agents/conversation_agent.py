import os
import asyncio
from typing import TypedDict, Annotated, List, Dict, Any, AsyncGenerator, Optional, Union
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
# from app.ai.agents.gen_test_cases import generate_test_cases_from_requirements
# from app.ai.agents.gen_requirements import generate_requirements_from_doc

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
    messages: Annotated[List[AnyMessage], add_messages]
    project_name: str
    context: str
    requirements: list
    testCases: list

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
    testCases_list = ["lol", "lmao"]
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

tools = [generate_testCases_fromRequirements_tool, generate_requirements_from_document_pdf_tool]
llm_with_tools = llm.bind_tools(tools)
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
    user_message_seq: int,
    session_agent_state: Optional[Dict[str, Any]] = None,
    project_name: str = "Default Project",
    use_tools: bool = True
) -> AsyncGenerator[str, None]:
    """
    Stream real LLM response using the conversation agent with HTTP streaming support.
    
    Args:
        session_id: Unique session identifier for memory persistence
        user_message: The user's input message
        user_message_seq: Sequence number of the user message
        session_agent_state: Current agent state from session
        project_name: Name of the project
        use_tools: Whether to use tools (requirements/test case generation)
    
    Yields:
        str: Content deltas for streaming response
    """
    logger.info(f"Starting agent response stream for session {session_id}")
    
    try:
        # Load or create agent state from session
        agent_state = session_agent_state or {}
        
        # Initialize conversation state if not exists
        if not agent_state.get("initialized"):
            main_system_prompt = load_main_system_prompt()
            conversation_state = AgentState(
                messages=[SystemMessage(content=main_system_prompt)],
                project_name=project_name,
                context=agent_state.get("context", ""),
                requirements=agent_state.get("requirements", []),
                testCases=agent_state.get("testCases", [])
            )
        else:
            # Restore conversation state from session
            conversation_state = AgentState(
                messages=[
                    SystemMessage(content=load_main_system_prompt()),
                    # Add previous messages if needed
                ],
                project_name=project_name,
                context=agent_state.get("context", ""),
                requirements=agent_state.get("requirements", []),
                testCases=agent_state.get("testCases", [])
            )
        
        # Add user message to conversation
        conversation_state["messages"].append(HumanMessage(content=user_message))
        
        # Stream the response using the agent with proper config
        config = {"configurable": {"thread_id": session_id}}
        
        if use_tools:
            # Use full agent with tools
            stream_response = graph.astream(
                conversation_state,
                config=config,  # type: ignore
                stream_mode="values"
            )
        else:
            # Use simple LLM without tools
            async for chunk in stream_simple_llm_response(user_message):
                yield chunk
            return
        
        # Process streaming response
        accumulated_content = ""
        async for chunk in stream_response:
            if "messages" in chunk and chunk["messages"]:
                last_message = chunk["messages"][-1]
                if isinstance(last_message, AIMessage):
                    # Extract content delta
                    if hasattr(last_message, 'content') and last_message.content:
                        new_content = str(last_message.content)
                        if new_content != accumulated_content:
                            delta = new_content[len(accumulated_content):]
                            accumulated_content = new_content
                            if delta:
                                yield delta
        
        # Return final agent state for session persistence
        final_state = {
            "initialized": True,
            "context": conversation_state.get("context", ""),
            "requirements": conversation_state.get("requirements", []),
            "testCases": conversation_state.get("testCases", []),
            "last_response": accumulated_content
        }
        
        # Store final state (this would need to be handled by the caller)
        # Since we can't directly update the session from here
        
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
        
        # Stream response from LLM
        stream_response = llm.astream(messages)
        
        async for chunk in stream_response:
            if hasattr(chunk, 'content') and chunk.content:
                yield str(chunk.content)
                
    except Exception as e:
        logger.error(f"Error in simple LLM response stream: {str(e)}")
        yield f"I apologize, but I encountered an error while processing your request: {str(e)}"

def get_agent_response(
    session_id: str,
    user_message: str,
    user_message_seq: int,
    session_agent_state: Optional[Dict[str, Any]] = None,
    project_name: str = "Default Project",
    use_tools: bool = True
) -> tuple[str, Dict[str, Any]]:
    """
    Get non-streaming agent response (for regular API calls).
    
    Args:
        session_id: Unique session identifier for memory persistence
        user_message: The user's input message
        user_message_seq: Sequence number of the user message
        session_agent_state: Current agent state from session
        project_name: Name of the project
        use_tools: Whether to use tools (requirements/test case generation)
    
    Returns:
        tuple: (response_content, updated_agent_state)
    """
    logger.info(f"Getting agent response for session {session_id}")
    
    try:
        # Load or create agent state from session
        agent_state = session_agent_state or {}
        
        # Initialize conversation state if not exists
        if not agent_state.get("initialized"):
            main_system_prompt = load_main_system_prompt()
            conversation_state = AgentState(
                messages=[SystemMessage(content=main_system_prompt)],
                project_name=project_name,
                context=agent_state.get("context", ""),
                requirements=agent_state.get("requirements", []),
                testCases=agent_state.get("testCases", [])
            )
        else:
            # Restore conversation state from session
            conversation_state = AgentState(
                messages=[
                    SystemMessage(content=load_main_system_prompt()),
                    # Add previous messages if needed
                ],
                project_name=project_name,
                context=agent_state.get("context", ""),
                requirements=agent_state.get("requirements", []),
                testCases=agent_state.get("testCases", [])
            )
        
        # Add user message to conversation
        conversation_state["messages"].append(HumanMessage(content=user_message))
        
        if use_tools:
            # Use full agent with tools
            config = {"configurable": {"thread_id": session_id}}
            response = graph.invoke(conversation_state, config=config)  # type: ignore
            
            # Extract AI response
            ai_response = ""
            if "messages" in response and response["messages"]:
                for msg in reversed(response["messages"]):
                    if isinstance(msg, AIMessage):
                        ai_response = str(msg.content)  # Ensure string type
                        break
            
            # Return final agent state
            final_agent_state = {
                "initialized": True,
                "context": response.get("context", ""),
                "requirements": response.get("requirements", []),
                "testCases": response.get("testCases", []),
                "last_response": ai_response
            }
            
            return ai_response, final_agent_state
            
        else:
            # Use simple LLM
            messages = [
                SystemMessage(content=load_main_system_prompt()),
                HumanMessage(content=user_message)
            ]
            response = llm.invoke(messages)
            ai_response = str(response.content)  # Ensure string type
            
            # Return simple agent state
            final_agent_state = {
                "initialized": True,
                "context": "",
                "requirements": [],
                "testCases": [],
                "last_response": ai_response
            }
            
            return ai_response, final_agent_state
            
    except Exception as e:
        logger.error(f"Error getting agent response: {str(e)}")
        error_response = f"I apologize, but I encountered an error while processing your request: {str(e)}"
        error_state = {
            "initialized": True,
            "context": "",
            "requirements": [],
            "testCases": [],
            "last_response": error_response,
            "error": str(e)
        }
        return error_response, error_state

def get_simple_llm_response(
    user_message: str,
    system_prompt: Optional[str] = None
) -> str:
    """
    Get simple LLM response without agent tools (fallback option).
    
    Args:
        user_message: The user's input message
        system_prompt: Optional system prompt (uses default if None)
    
    Returns:
        str: The LLM response content
    """
    logger.info("Getting simple LLM response")
    
    try:
        # Create a simple conversation with the LLM
        messages = [
            SystemMessage(content=system_prompt or load_main_system_prompt()),
            HumanMessage(content=user_message)
        ]
        
        # Get response from LLM
        response = llm.invoke(messages)
        return str(response.content)  # Ensure string type
        
    except Exception as e:
        logger.error(f"Error getting simple LLM response: {str(e)}")
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"

# Helper function to initialize agent state
def initialize_agent_state(
    project_name: str = "Default Project",
    context: str = "",
    requirements: Optional[List[Dict]] = None,
    testCases: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Initialize a new agent state.
    
    Args:
        project_name: Name of the project
        context: Project context/summary
        requirements: List of requirements
        testCases: List of test cases
    
    Returns:
        Dict: Initialized agent state
    """
    return {
        "initialized": True,
        "project_name": project_name,
        "context": context,
        "requirements": requirements or [],
        "testCases": testCases or [],
        "last_response": ""
    }