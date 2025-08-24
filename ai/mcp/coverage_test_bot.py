import os
import json
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END


load_dotenv()
google_llm_api_key = os.getenv("GOOGLE_API_KEY")
api_max_tokens = 64000


# 1) Define the shape of our shared state
class AgentState(TypedDict, total=False):
    project_id: str
    requirements_content: str
    rtm_content: str
    test_cases_content: str
    requirements_list: List[Dict[str, Any]]
    test_cases_list: List[Dict[str, Any]]
    mapping: List[Dict[str, Any]]
    requirement_coverage: Dict[str, Any]
    feature_coverage: Dict[str, Any]
    high_risk_coverage: Dict[str, Any]
    report_content: Dict[str, Any]

# 2) Initialize a zero-temperature LLM for deterministic JSON extraction
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature = 0.0,
    max_tokens = api_max_tokens,
    api_key = google_llm_api_key
)


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
      [{ "id": "...", "title": "...", "description": "...", "category": "...", "risk": "...", "dependencies": "..." }, …]
    """
    prompt = f"""
    Extract a JSON array of requirements from the markdown below.
    Each item must have "id", "title", "description", "category", "risk", and "dependencies" fields.

    ```markdown
    {state['requirements_content']}
    """
    resp = llm.invoke([HumanMessage(content=prompt)])
    reqs = json.loads(resp.content)
    return {"requirements_list": reqs}

def extract_test_cases(state: AgentState) -> AgentState:
    """
    Ask the LLM to parse the test cases MD and return JSON:
    [
      {
        "test_case_id": "...",
        "requirement_id": "...",
        "category": "...",
        "test_case_description": "...",
        "test_type": "...",
        "test_steps": "...",
        "priority": "...",
        "preconditions": "...",
        "expected_result": "..."
      },
      ...
    ]
    """
    prompt = f"""
    Extract a JSON array of test cases from the markdown below.
    Each item must have the following fields:
    "test_case_id", "requirement_id", "category", "test_case_description", "test_type", "test_steps", "priority", "preconditions", "expected_result".

    ```markdown
    {state['test_cases_content']}
    """
    resp = llm.invoke([HumanMessage(content=prompt)])
    tcs = json.loads(resp.content)
    return {"test_cases_list": tcs}

def build_mapping(state: AgentState) -> AgentState:
    """ Build a per-requirement map of which test cases cover it. """ 
    mapping = [] 
    for req in state["requirements_list"]:
        rid = req["id"]
        covered = [tc["test_case_id"] for tc in state["test_cases_list"] if tc["requirement_id"] == rid]
        mapping.append({"requirement_id": rid, "covered_by": covered})
    return {"mapping": mapping}

def requirement_coverage_metrics(state: AgentState) -> AgentState:
    """ Compute total/covered/percent for requirements. """ 
    total = len(state["requirements_list"]) 
    covered = sum(1 for m in state["mapping"] if m["covered_by"]) 
    pct = covered / total * 100 if total else 0.0 
    return { "requirement_coverage": { "total_requirements": total, "covered_requirements": covered, "requirement_coverage_percent": round(pct, 2), } }

def feature_coverage_metrics(state: AgentState) -> AgentState:
    """
    Measures the percentage of functional requirements (features) that are covered by at least one test case.
    Calculation: (number of functional requirements with at least one covering test case) / (total functional requirements)
    """
    functional_reqs = [r for r in state["requirements_list"] if r.get("category", "").strip().lower() == "functional"]
    total_functional = len(functional_reqs)
    covered_functional = sum(
        1 for r in functional_reqs
        if any(m["requirement_id"] == r["id"] and m["covered_by"] for m in state["mapping"])
    )
    pct = covered_functional / total_functional * 100 if total_functional else 0.0
    return {
        "feature_coverage": {
            "total_functional_requirements": total_functional,
            "covered_functional_requirements": covered_functional,
            "functional_coverage_percent": round(pct, 2),
        }
    }

def high_risk_coverage_metrics(state: AgentState) -> AgentState:
    # "High" risk requirements coverage
    high_risk_reqs = [r for r in state["requirements_list"] if r.get("risk", "").strip().lower() == "high"]
    total = len(high_risk_reqs)
    covered = sum(
        1 for r in high_risk_reqs
        if any(m["requirement_id"] == r["id"] and m["covered_by"] for m in state["mapping"])
    )
    pct = covered / total * 100 if total else 0.0
    return {
        "high_risk_coverage": {
            "total_high_risk_requirements": total,
            "covered_high_risk_requirements": covered,
            "high_risk_coverage_percent": round(pct, 2),
        }
    }

def generate_report(state: AgentState) -> AgentState: 
    # Compose a structured JSON report
    report = {
        "requirement_coverage": state.get("requirement_coverage", {}),
        "feature_coverage": state.get("feature_coverage", {}),
        "high_risk_coverage": state.get("high_risk_coverage", {}),
        "requirement_to_testcase_mapping": state.get("mapping", []),
    }
    return {"report_content": report}

def write_report(state: AgentState) -> AgentState: 
    """ Save the report as data/project-<id>/artifacts/test_coverage_result.md """ 
    base = f"data/project-{state['project_id']}/artifacts" 
    os.makedirs(base, exist_ok=True) 
    out_path = os.path.join(base, "test_coverage_result.json") 
    with open(out_path, "w", encoding="utf-8") as f: 
        json.dump(state["report_content"], f, indent=2)
    return {}

def run_coverage_test(project_id: str) -> Dict[str, Any]:
    """
    Runs the full coverage analysis pipeline for the given project_id.
    Returns the report content as a Python dict.
    EXAMPLE OUTPUT DICTIONARY:
    {
        "requirement_coverage": {
            "total_requirements": 10,
            "covered_requirements": 5,
            "coverage_percent": 50.0
        },
        "feature_coverage": {
            "total_functional_requirements": 8,
            "covered_functional_requirements": 4,
            "functional_coverage_percent": 50.0
        },
        "high_risk_coverage": {
            "total_high_risk_requirements": 5,
            "covered_high_risk_requirements": 2,
            "high_risk_coverage_percent": 40.0
        },
        "requirement_to_testcase_mapping": [
            {
                "requirement_id": REQ_1,
                "testcase_ids": [101, 102]
            },
            {
                "requirement_id": REQ_2,
                "testcase_ids": [103]
            },
            {
                "requirement_id": REQ_ 3,
                "testcase_ids": []
            }
        ],

    }
    """
    builder = StateGraph(AgentState)
    builder.add_node(load_files, "load_files")
    builder.add_node(extract_requirements, "extract_requirements")
    builder.add_node(extract_test_cases, "extract_test_cases")
    builder.add_node(build_mapping, "build_mapping")
    builder.add_node(requirement_coverage_metrics, "requirement_coverage_metrics")
    builder.add_node(feature_coverage_metrics, "feature_coverage_metrics")
    builder.add_node(high_risk_coverage_metrics, "high_risk_coverage_metrics")
    builder.add_node(generate_report, "generate_report")
    builder.add_node(write_report, "write_report")

    builder.add_edge(START, "load_files")
    builder.add_edge("load_files", "extract_requirements")
    builder.add_edge("extract_requirements", "extract_test_cases")
    builder.add_edge("extract_test_cases", "build_mapping")
    builder.add_edge("build_mapping", "requirement_coverage_metrics")
    builder.add_edge("requirement_coverage_metrics", "feature_coverage_metrics")
    builder.add_edge("feature_coverage_metrics", "high_risk_coverage_metrics")
    builder.add_edge("high_risk_coverage_metrics", "generate_report")
    builder.add_edge("generate_report", "write_report")
    builder.add_edge("write_report", END)

    graph = builder.compile()
    final_state = graph.invoke({"project_id": project_id})
    return final_state["report_content"]

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("--project_id", required=True, help="Your project identifier") 
    args = parser.parse_args()

    builder = StateGraph(AgentState) 
    builder.add_node(load_files, "load_files") 
    builder.add_node(extract_requirements, "extract_requirements") 
    builder.add_node(extract_test_cases, "extract_test_cases") 
    builder.add_node(build_mapping, "build_mapping") 
    builder.add_node(requirement_coverage_metrics, "requirement_coverage_metrics") 
    builder.add_node(feature_coverage_metrics, "feature_coverage_metrics") 
    builder.add_node(high_risk_coverage_metrics, "high_risk_coverage_metrics") 
    builder.add_node(generate_report, "generate_report") 
    builder.add_node(write_report, "write_report")

    builder.add_edge(START, "load_files") 
    builder.add_edge("load_files", "extract_requirements") 
    builder.add_edge("extract_requirements", "extract_test_cases") 
    builder.add_edge("extract_test_cases", "build_mapping") 
    builder.add_edge("build_mapping", "requirement_coverage_metrics") 
    builder.add_edge("requirement_coverage_metrics", "feature_coverage_metrics") 
    builder.add_edge("feature_coverage_metrics", "high_risk_coverage_metrics") 
    builder.add_edge("high_risk_coverage_metrics", "generate_report") 
    builder.add_edge("generate_report", "write_report") 
    builder.add_edge("write_report", END)

    graph = builder.compile() 
    graph.invoke({"project_id": args.project_id})

if __name__ == "__main__": main()