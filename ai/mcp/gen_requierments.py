import os
import json
import base64
from langchain_anthropic import ChatAnthropic
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv



load_dotenv()
llm_api_key = os.getenv("ANTHROPIC_API_KEY")
api_max_tokens = 64000                      # Maximum ammount


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature = 0.3,
    max_tokens = api_max_tokens,
    api_key = llm_api_key
)

def generate_requirements_from_doc(
    path_to_document_pdf: str,
    path_to_initPrompt_1: str,
    path_to_initPrompt_2: str, 
    path_to_reflectionArewrite_Prompt: str,
    path_to_summaryPrompt: str,
    output_requirements_md_path: str,
    output_context_md_path: str
) -> tuple[str, str]:
    """
    Generate requirements from a PDF document using AI analysis and save directly to Markdown files.
    
    Params: 
        path_to_document_pdf (str): Path to the PDF document to analyze
        path_to_initPrompt_1 (str): Path to the first initial prompt file
        path_to_initPrompt_2 (str): Path to the second initial prompt file
        path_to_reflectionArewrite_Prompt (str): Path to the reflection and rewrite prompt file
        path_to_summaryPrompt (str): Path to the context summary prompt file
        output_requirements_md_path (str): Path where the requirements.md file will be saved
        output_context_md_path (str): Path where the context summary.md file will be saved

    Output:
        tuple: (path to requirements.md file, path to context summary.md file)
    """


    """
    1. Load the prompts
        Prompt CONTENT are written to satisfy Athropic model.
    """
    with open(path_to_initPrompt_1,"r") as f:
        initPrompt_1 = f.read()

    with open(path_to_initPrompt_2,"r") as f:
        initPrompt_2 = f.read()
    
    
    try:
        if not os.path.isfile(path_to_document_pdf):
            raise FileNotFoundError(f"File not found: {path_to_document_pdf}")
        with open(path_to_document_pdf, 'rb') as f:
            pdf_in_base64_encoded_string = base64.standard_b64encode(f.read()).decode('utf-8')
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except PermissionError:
        print("Error: Permission denied when trying to read the file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    content_prompt_initial = [
                    {
                        "type": "text",
                        "text": initPrompt_1
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_in_base64_encoded_string
                        },
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": initPrompt_2
                    }
                ]

    with open(path_to_reflectionArewrite_Prompt,"r") as f:
        reflection_and_rewrite_Prompt = f.read()
        content_prompt_reflection_and_rewrite = [
                    {
                        "type": "text",
                        "text": reflection_and_rewrite_Prompt
                    }
                ]
    with open(path_to_summaryPrompt,"r") as f:
        summary_Prompt = f.read()
        content_prompt_summary = [
                    {
                        "type": "text",
                        "text": summary_Prompt
                    }
                ]        

    """
    2. Define writing Steps
    """
    def write_initial_draft(state: AgentState):
        model_response = llm.invoke([HumanMessage(content=content_prompt_initial)])
        
        return {"messages": [HumanMessage(content=content_prompt_initial), model_response]}
        
    def write_reflection_and_final(state: AgentState):
        prompt_messages = state['messages'] + [HumanMessage(content=reflection_and_rewrite_Prompt)]
        model_response = llm.invoke(prompt_messages)

        return{"messages": [HumanMessage(content=reflection_and_rewrite_Prompt), model_response]}

    def write_summary(state: AgentState):
        prompt_messages = state['messages'] + [HumanMessage(content=summary_Prompt)] + [AIMessage(content="[")]
        model_response = llm.invoke(prompt_messages)

        return{"messages": [HumanMessage(content=summary_Prompt), model_response]}

    """
    3. Build graph
    """
    builder = StateGraph(AgentState)
    builder.add_node("write_initial_draft", write_initial_draft)
    builder.add_node("write_reflection_and_final", write_reflection_and_final)
    builder.add_node("write_summary", write_summary)
    builder.add_edge(START, "write_initial_draft")
    builder.add_edge("write_initial_draft","write_reflection_and_final")
    builder.add_edge("write_reflection_and_final","write_summary")
    builder.add_edge("write_summary", END)

    graph = builder.compile()


    """
    4. Invoke
    """
    langchainConfig_messages = graph.invoke({"messages": []})
    # for message in langchainConfig_messages['messages']:
    #     print(message)

    """
    5. Output Parsing and File Writing
    """
    
    # Extract the final requirements content (should be in Markdown format)
    output_requirements_md_content = langchainConfig_messages['messages'][-3].content
    output_context_md_content = langchainConfig_messages['messages'][-1].content

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(output_requirements_md_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_context_md_path), exist_ok=True)
    
    # Write requirements to Markdown file
    try:
        with open(output_requirements_md_path, 'w', encoding='utf-8') as f:
            f.write(output_requirements_md_content)
        print(f"Requirements successfully written to: {output_requirements_md_path}")
    except Exception as e:
        print(f"Error writing requirements file: {e}")
        raise

    # Write context summary to Markdown file  
    try:
        with open(output_context_md_path, 'w', encoding='utf-8') as f:
            f.write(output_context_md_content)
        print(f"Context summary successfully written to: {output_context_md_path}")
    except Exception as e:
        print(f"Error writing context file: {e}")
        raise

    return output_requirements_md_path, output_context_md_path
