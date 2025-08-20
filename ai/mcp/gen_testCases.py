
from langchain_anthropic import ChatAnthropic
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, AIMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os


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

def generate_test_cases_from_rtm(rtm_content: str, 
                                path_to_initPrompt_1:str,
                                path_to_initPrompt_2:str,
                                path_to_reflectionPrompt:str,
                                path_to_finalPrompt:str,
                                out_path:str) -> str:
    """
    Generates test cases from RTM content and writes them to a file.

    Parameters:
    - rtm_content (str): RTM Markdown content.
    - out_path (str): Path to save the generated test cases JSON.

    Returns:
    - str: Path to the saved test cases file.
    """

    from langchain_core.messages import HumanMessage
    from langgraph.graph import StateGraph, START, END

    # Load prompts
    with open(path_to_initPrompt_1, 'r') as f:
        init_1 = f.read()
    with open(path_to_initPrompt_2, 'r') as f:
        init_2 = f.read()
    with open(path_to_reflectionPrompt, 'r') as f:
        reflection = f.read()
    with open(path_to_finalPrompt, 'r') as f:
        final = f.read()

    # Prompt content
    content_initial= [
        {"type": "text", "text": init_1},
        {"type": "text", "text": rtm_content},
        {"type": "text", "text": init_2}
    ]
    content_reflection = [{"type": "text", "text": reflection}]
    content_final = [{"type": "text", "text": final}]

    # Step functions
    def write_initial_draft(state: AgentState):
        response = llm.invoke([HumanMessage(content=content_initial)])
        return {"messages": [HumanMessage(content=content_initial), response]}

    def write_reflection(state: AgentState):
        response = llm.invoke(state["messages"] + [HumanMessage(content=content_reflection)])
        return {"messages": state["messages"] + [HumanMessage(content=content_reflection), response]}

    def write_final(state: AgentState):
        response = llm.invoke(state["messages"] + [HumanMessage(content=content_final)])
        return {"messages": state["messages"] + [HumanMessage(content=content_final), response]}

    # Build and run graph
    builder = StateGraph(AgentState)
    builder.add_node(write_initial_draft, "write_initial_draft")
    builder.add_node(write_reflection, "write_reflection")
    builder.add_node(write_final, "write_final")
    builder.add_edge(START, "write_initial_draft")
    builder.add_edge("write_initial_draft", "write_reflection")
    builder.add_edge("write_reflection", "write_final")
    builder.add_edge("write_final", END)
    graph = builder.compile()

    result = graph.invoke({"messages": []})
    final_output = result["messages"][-1].content


    # Create directories if they don't exist
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    #Write to file
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(final_output)
        print(f"Requirements successfully written to: {out_path}")
    except Exception as e:
        print(f"Error writing requirements file: {e}")
        raise

    return out_path