
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, AIMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os


load_dotenv()
anthropic_llm_api_key = os.getenv("ANTHROPIC_API_KEY")
google_llm_api_key = os.getenv("GOOGLE_API_KEY")
api_max_tokens = 64000                      # Maximum ammount


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# llm = ChatAnthropic(
#     model="claude-3-7-sonnet-latest",
#     temperature = 0.3,
#     max_tokens = anthropic_llm_api_key,
#     api_key = llm_api_key
# )
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    max_tokens = None,
    api_key = google_llm_api_key,
)

def generate_test_cases_from_rtm(
    rtm_content: str, 
    path_to_initPrompt_1: str,
    path_to_initPrompt_2: str,
    path_to_reflectionPrompt: str,
    path_to_finalPrompt: str,
    out_path: str,
    max_chunk_tokens: int = 12000,
    delay_seconds: int = 3
) -> str:
    """
    Generates test cases from RTM content and writes them to a file.
    If the RTM is too large, splits it into smaller chunks and aggregates the results.

    Parameters:
    - rtm_content (str): RTM Markdown content.
    - out_path (str): Path to save the generated test cases JSON.
    - max_chunk_tokens (int): Maximum tokens per chunk (default: 12000).
    - delay_seconds (int): Delay in seconds between chunk API calls (default: 3).

    Returns:
    - str: Path to the saved test cases file.
    """

    from langchain_core.messages import HumanMessage
    from langgraph.graph import StateGraph, START, END
    import tiktoken
    import json
    import time

    # Helper to estimate token count (using tiktoken or fallback)
    def estimate_tokens(text):
        try:
            enc = tiktoken.encoding_for_model("claude-3-7-sonnet")
            return len(enc.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return max(1, len(text) // 4)

    # Helper to split RTM table into row chunks
    def split_rtm_table(rtm_md: str, max_tokens: int):
        lines = rtm_md.strip().splitlines()
        if len(lines) < 3:
            return [rtm_md]
        header = lines[0]
        sep = lines[1]
        rows = lines[2:]
        chunks = []
        current = [header, sep]
        current_tokens = estimate_tokens('\n'.join(current))
        for row in rows:
            row_tokens = estimate_tokens(row)
            if current_tokens + row_tokens > max_tokens and len(current) > 2:
                chunks.append('\n'.join(current))
                current = [header, sep, row]
                current_tokens = estimate_tokens('\n'.join(current))
            else:
                current.append(row)
                current_tokens += row_tokens
        if len(current) > 2:
            chunks.append('\n'.join(current))
        return chunks

    # Load prompts
    with open(path_to_initPrompt_1, 'r') as f:
        init_1 = f.read()
    with open(path_to_initPrompt_2, 'r') as f:
        init_2 = f.read()
    with open(path_to_reflectionPrompt, 'r') as f:
        reflection = f.read()
    with open(path_to_finalPrompt, 'r') as f:
        final = f.read()

    # Step functions (same as before)
    def build_graph(content_initial, content_reflection, content_final):
        def write_initial_draft(state: AgentState):
            response = llm.invoke([HumanMessage(content=content_initial)])
            return {"messages": [HumanMessage(content=content_initial), response]}

        def write_reflection(state: AgentState):
            response = llm.invoke(state["messages"] + [HumanMessage(content=content_reflection)])
            return {"messages": state["messages"] + [HumanMessage(content=content_reflection), response]}

        def write_final(state: AgentState):
            response = llm.invoke(state["messages"] + [HumanMessage(content=content_final)])
            return {"messages": state["messages"] + [HumanMessage(content=content_final), response]}

        builder = StateGraph(AgentState)
        builder.add_node(write_initial_draft, "write_initial_draft")
        builder.add_node(write_reflection, "write_reflection")
        builder.add_node(write_final, "write_final")
        builder.add_edge(START, "write_initial_draft")
        builder.add_edge("write_initial_draft", "write_reflection")
        builder.add_edge("write_reflection", "write_final")
        builder.add_edge("write_final", END)
        return builder.compile()

    # Split RTM if needed
    rtm_chunks = split_rtm_table(rtm_content, max_chunk_tokens)

    all_markdown = []
    for i, chunk in enumerate(rtm_chunks):
        content_initial = [
            {"type": "text", "text": init_1},
            {"type": "text", "text": chunk},
            {"type": "text", "text": init_2}
        ]
        content_reflection = [{"type": "text", "text": reflection}]
        content_final = [{"type": "text", "text": final}]
        graph = build_graph(content_initial, content_reflection, content_final)
        result = graph.invoke({"messages": []})
        final_output = result["messages"][-1].content
        # Clean up Markdown: only keep header for first chunk
        if isinstance(final_output, str):
            lines = final_output.strip().splitlines()
        else:
            lines = str(final_output).strip().splitlines()
        if i == 0:
            # Keep all lines for the first chunk
            all_markdown.extend(lines)
        else:
            # Remove header and separator lines (assume header is first 2 lines)
            if len(lines) > 2:
                all_markdown.extend(lines[2:])
            else:
                all_markdown.extend(lines)
        # Add delay between chunk calls to avoid rate limit
        if i < len(rtm_chunks) - 1:
            time.sleep(delay_seconds)

    # Write aggregated Markdown to file
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_markdown))
        print(f"Test cases successfully written to: {out_path}")
    except Exception as e:
        print(f"Error writing test cases file: {e}")
        raise

    return out_path

