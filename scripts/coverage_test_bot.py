import os
import json
import argparse
from typing import TypedDict, Annotated, List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

# 1) Define the shape of our shared state
class AgentState(TypedDict, total=False):
    project_id: str
    requirements_content: str
    rtm_content: str
    test_cases_content: str
    requirements_list: List[Dict]
    test_cases_list: List[Dict]
    mapping: List[Dict]
    coverage_metrics: Dict
    report_content: str

# 2) Initialize a zero-temperature LLM for deterministic JSON extraction
llm = ChatGoogleGenerativeAI(model="gpt-4", temperature=0.0, max_tokens=2048)

def load_files(state: AgentState) -> AgentState:
    """
    Load the three markdown artifacts into memory.
    """
    base = f"data/project-{state['project_id']}/artifacts"
    paths = {
        "requirements_content": os.path.join(base, "requirement.md"),
        "rtm_content":        os.path.join(base, "requirements_traceability_matrix.md"),
        "test_cases_content": os.path.join(base, "test_cases.md"),
    }
    out: AgentState = {}
    for key, p in paths.items():
        with open(p, "r", encoding="utf-8") as f:
            out[key] = f.read()
    return out

def extract_requirements(state: AgentState) -> AgentState:
    """
    Ask the LLM to parse the requirements MD and return JSON:
      [{ "id": "RQ-01", "description": "..." }, …]
    """
    prompt = f"""
    Extract a JSON array of requirements from the markdown below.
    Each item must have "id" and "description" fields.

    ```markdown
    {state['requirements_content']}
    """ 
    resp = llm.invoke([HumanMessage(content=prompt)]) 
    reqs = json.loads(resp.content) 
    return {"requirements_list": reqs}

def extract_test_cases(state: AgentState) -> AgentState: 
    """ Ask the LLM to parse the test cases MD and return JSON: 
    [{ "tc_id": "TC-01", "description": "...", "covered_requirements": ["RQ-01","RQ-02"] }, …] """ 
    prompt = f""" Extract a JSON array of test cases from the markdown below. Each item must have:
    "tc_id"
    "description"
    "covered_requirements" (array of requirement IDs)
    {state['test_cases_content']}
    """ 
    resp = llm.invoke([HumanMessage(content=prompt)]) 
    tcs = json.loads(resp.content) 
    return {"test_cases_list": tcs}

def build_mapping(state: AgentState) -> AgentState: 
    """ Build a per-requirement map of which test cases cover it. """ 
    mapping = [] 
    for req in state["requirements_list"]: rid = req["id"] 
    covered = [ tc["tc_id"] for tc in state["test_cases_list"] if rid in tc.get("covered_requirements", []) ] 
    mapping.append({"requirement_id": rid, "covered_by": covered}) 
    return {"mapping": mapping}

def calculate_metrics(state: AgentState) -> AgentState: 
    """ Compute total/covered/percent for requirements. """ 
    total = len(state["requirements_list"]) 
    covered = sum(1 for m in state["mapping"] if m["covered_by"]) 
    pct = covered / total * 100 if total else 0.0 
    return { "coverage_metrics": { "total_requirements": total, "covered_requirements": covered, "requirement_coverage_percent": round(pct, 2), } }

def generate_report(state: AgentState) -> AgentState: 
    """ Render a Markdown report with summary metrics and per-RQ details. """ 
    m = state["coverage_metrics"] 
    lines = [ "# Test Coverage Report", "", f"- Total Requirements: {m['total_requirements']}", f"- Covered Requirements: {m['covered_requirements']}", f"- Requirement Coverage: {m['requirement_coverage_percent']}%", "", "## Requirement-to-TestCase Mapping", "", ] 
    for row in state["mapping"]: covered = ", ".join(row["covered_by"]) or "None" 
    lines.append(f"- {row['requirement_id']} covered by: {covered}") 
    return {"report_content": "\n".join(lines)}

def write_report(state: AgentState) -> AgentState: 
    """ Save the report as data/project-<id>/artifacts/test_coverage_result.md """ 
    base = f"data/project-{state['project_id']}/artifacts" 
    os.makedirs(base, exist_ok=True) 
    out_path = os.path.join(base, "test_coverage_result.md") 
    with open(out_path, "w", encoding="utf-8") as f: 
        f.write(state["report_content"]) 
    return {}

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("--project_id", required=True, help="Your project identifier") 
    args = parser.parse_args()


    builder = StateGraph(AgentState) 
    builder.add_node(load_files, "load_files") 
    builder.add_node(extract_requirements, "extract_requirements") 
    builder.add_node(extract_test_cases, "extract_test_cases") 
    builder.add_node(build_mapping, "build_mapping") 
    builder.add_node(calculate_metrics, "calculate_metrics") 
    builder.add_node(generate_report, "generate_report") 
    builder.add_node(write_report, "write_report")

    builder.add_edge(START, "load_files") 
    builder.add_edge("load_files", "extract_requirements") 
    builder.add_edge("extract_requirements", "extract_test_cases") 
    builder.add_edge("extract_test_cases", "build_mapping") 
    builder.add_edge("build_mapping", "calculate_metrics") 
    builder.add_edge("calculate_metrics", "generate_report") 
    builder.add_edge("generate_report", "write_report") 
    builder.add_edge("write_report", END)

    graph = builder.compile() 
    graph.invoke({"project_id": args.project_id})

if __name__ == "main": main()