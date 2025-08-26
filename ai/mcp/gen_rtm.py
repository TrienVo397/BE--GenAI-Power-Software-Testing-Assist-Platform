# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\ai\mcp\gen_rtm.py
import os
from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()
llm_api_key = os.getenv("ANTHROPIC_API_KEY")
api_max_tokens = 64000                      # Maximum ammount


class RTMAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# llm = ChatDeepSeek(
#     model="deepseek-chat",
#     temperature=0.2,
#     max_tokens=api_max_tokens,
#     timeout=60,
#     max_retries=2,
# )

llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature = 0.3,
    max_tokens = api_max_tokens,
    api_key = llm_api_key
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
        
        logger.info("Generating Requirements Traceability Matrix ...")
        
        # Generate RTM using AI
        response = llm.invoke(messages)
        logger.info(f"AI response received, type: {type(response)}")
        
        # Handle different response content types safely
        try:
            if hasattr(response, 'content'):
                content = response.content
                logger.info(f"Response content type: {type(content)}")
                
                if isinstance(content, list):
                    logger.info(f"Content is list with {len(content)} items")
                    # Handle list of content blocks (common in newer LangChain versions)
                    rtm_content = ""
                    for i, block in enumerate(content):
                        logger.info(f"Block {i} type: {type(block)}")
                        if hasattr(block, 'text'):
                            rtm_content += str(getattr(block, 'text', ''))
                        elif isinstance(block, dict) and 'text' in block:
                            rtm_content += str(block['text'])
                        else:
                            rtm_content += str(block)
                elif isinstance(content, str):
                    rtm_content = content
                    logger.info("Content is string")
                else:
                    rtm_content = str(content)
                    logger.info(f"Content converted to string from {type(content)}")
            else:
                rtm_content = str(response)
                logger.info("No content attribute, using full response")
            
            logger.info(f"RTM content generated successfully, length: {len(rtm_content)} characters")
            
        except Exception as content_error:
            logger.error(f"Error processing AI response content: {content_error}")
            logger.exception("Content processing error details:")
            # Fallback to string conversion
            rtm_content = str(response)
            logger.info(f"Using fallback string conversion, length: {len(rtm_content)} characters")
        
        # Validate that we have actual content
        if not rtm_content or len(rtm_content.strip()) < 10:
            raise Exception("Generated RTM content is empty or too short")
        
        # Save the generated RTM to file
        try:
            output_dir = os.path.dirname(output_rtm_md_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_rtm_md_path, 'w', encoding='utf-8') as f:
                f.write(rtm_content)
            
            # Verify the file was written correctly
            if os.path.exists(output_rtm_md_path):
                with open(output_rtm_md_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                if len(saved_content) != len(rtm_content):
                    logger.warning(f"File length mismatch: expected {len(rtm_content)}, got {len(saved_content)}")
            else:
                raise Exception("RTM file was not created successfully")
            
            logger.info(f"Requirements Traceability Matrix generated and saved to: {output_rtm_md_path}")
            
        except Exception as write_error:
            logger.error(f"Failed to write RTM file: {write_error}")
            raise Exception(f"Failed to save RTM file: {str(write_error)}")
        
        return rtm_content
        
    except FileNotFoundError as e:
        error_msg = f"Required file not found: {e}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    except PermissionError as e:
        error_msg = f"Permission denied accessing file: {e}"
        logger.error(error_msg)
        raise PermissionError(error_msg)
    except OSError as e:
        error_msg = f"File system error: {e}"
        logger.error(error_msg)
        raise OSError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error generating Requirements Traceability Matrix: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
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
