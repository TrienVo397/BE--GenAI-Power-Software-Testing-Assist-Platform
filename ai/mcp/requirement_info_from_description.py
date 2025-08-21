import os
import re
import ast
from urllib import response
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

def parse_markdown_requirements(md_path: str) -> list:
    """
    Parse the requirements Markdown file and return a list of requirement dictionaries.
    """
    if not os.path.exists(md_path):
        return []
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    # Extract Markdown table
    table_match = re.search(r"\|.*?\|\n\|[-| ]+\|\n((?:\|.*\|\n?)+)", md_text, re.DOTALL)
    if not table_match:
        return []
    table = table_match.group(0).strip().split('\n')
    headers = [h.strip() for h in table[0].split('|')[1:-1]]
    requirements = []
    for row in table[2:]:  # skip header and separator
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) == len(headers):
            requirements.append(dict(zip(headers, cols)))
    return requirements

def requirement_info_from_description(description: str, requirements_md_path: str) -> str:
    """
    Given a description and a path to the requirements Markdown file,
    use an LLM to find and return requirements that align with the description.
    """
    requirements_list = parse_markdown_requirements(requirements_md_path)
    if not requirements_list:
        return "[]"
    
    load_dotenv()
    llm_api_key = os.getenv("ANTHROPIC_API_KEY")
    api_max_tokens = 64000                      # Maximum ammount
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-latest",
        temperature = 0.3,
        max_tokens = api_max_tokens,
        api_key = llm_api_key
    )

    system_message = """
    You are provided with a `description` string that outlines a specific QA need or objective in the context of the Software Development Life Cycle (SDLC). You also receive a list of `requirements`, where each requirement is a dictionary with attributes such as "test id", "priority".

    Your task is to:
    1. Analyze the `description` and infer its intended QA function or goal.
    2. Scan the list of requirement dictionaries.
    3. Identify which requirements are semantically aligned with the description.
    4. Copy the dictionary of that requirement and add it onto a Python list
    5. Return a list containing the full dictionaries of matching requirements. ONLY return the list and nothing else

    Example:
    description = "Looking for requirements related to test automation during the integration phase"
    requirements = [
    {"id": "R1", "type": "manual testing", "objective": "exploratory testing", "phase": "system testing", "tool": "none", "priority": "medium", "owner": "QA team"},
    {"id": "R2", "type": "automated testing", "objective": "regression coverage", "phase": "integration testing", "tool": "Selenium", "priority": "high", "owner": "QA automation lead"},
    {"id": "R3", "type": "code review", "objective": "quality gate", "phase": "development", "tool": "SonarQube", "priority": "low", "owner": "Dev lead"}
    ]

    Expected output:
    [
    {"id": "R2", "type": "automated testing", "objective": "regression coverage", "phase": "integration testing", "tool": "Selenium", "priority": "high", "owner": "QA automation lead"}
    ]
    """
    messages = [SystemMessage(content=system_message)]
    messages.append(HumanMessage(content="here is the description: " + description + " Here is the requirement list: " + str(requirements_list)))
    response = llm.invoke(messages)
    return response