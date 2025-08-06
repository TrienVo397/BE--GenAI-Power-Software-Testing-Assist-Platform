# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\ai\mcp\gen_rtm.py
import os
from langchain_deepseek import ChatDeepSeek
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
api_max_tokens = 32000

class RTMAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.2,
    max_tokens=api_max_tokens,
    timeout=60,
    max_retries=2,
)

def generate_rtm_from_requirements(
    requirements_content: str,
    context_content: str,
    rtm_prompt_path: str,
    output_rtm_md_path: str
) -> str:
    """
    Generate a Requirements Traceability Matrix (RTM) from requirements using AI analysis.
    
    Args:
        requirements_content (str): The requirements document content in Markdown
        context_content (str): The context summary content
        rtm_prompt_path (str): Path to the RTM generation prompt file
        output_rtm_md_path (str): Path where the generated RTM will be saved
        
    Returns:
        str: The generated Requirements Traceability Matrix content
    """
    try:
        # Read the RTM generation prompt
        with open(rtm_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        # Prepare the user message with requirements and context
        user_message = f"""
**Requirements Document:**
{requirements_content}

**Context Summary:**
{context_content}

Please generate a comprehensive Requirements Traceability Matrix (RTM) based on the above requirements and context.
        """
        
        # Create messages for the conversation
        messages = [
            ("system", system_prompt),
            ("user", user_message)
        ]
        
        logger.info("Generating Requirements Traceability Matrix using ChatDeepSeek...")
        
        # Generate RTM using AI
        response = llm.invoke(messages)
        rtm_content = str(response.content)  # Ensure string type
        
        # Save the generated RTM to file
        os.makedirs(os.path.dirname(output_rtm_md_path), exist_ok=True)
        with open(output_rtm_md_path, 'w', encoding='utf-8') as f:
            f.write(rtm_content)
        
        logger.info(f"Requirements Traceability Matrix generated and saved to: {output_rtm_md_path}")
        return rtm_content
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error generating Requirements Traceability Matrix: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def rtm_agent(state: RTMAgentState):
    """
    RTM generation agent for LangGraph integration.
    """
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Create the RTM generation graph
rtm_graph = StateGraph(RTMAgentState)
rtm_graph.add_node("rtm_agent", rtm_agent)
rtm_graph.add_edge(START, "rtm_agent")
rtm_graph.add_edge("rtm_agent", END)

rtm_chain = rtm_graph.compile()
