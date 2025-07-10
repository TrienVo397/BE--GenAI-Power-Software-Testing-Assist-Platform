import os
from typing import TypedDict, Annotated, List, Dict, Any
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

# Example initialization (for reference, not run at import)
# with open("app/ai/prompts/main_system_prompt.txt", "r") as f:
#     main_system_prompt = f.read()
# currState = AgentState(
#     messages=[SystemMessage(content=main_system_prompt)],
#     project_name="QA_automation",
#     testCases=