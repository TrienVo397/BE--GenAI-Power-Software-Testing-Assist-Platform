import os
import re

def change_requirement_info(md_path: str, req_id: str, attribute: str, value: str) -> tuple[bool, str]:
    """
    Update a requirement's attribute in a Markdown table by req_id and attribute name.
    Returns (True, "") on success, (False, error_message) on failure.
    """
    if not os.path.exists(md_path):
        return False, "Requirements file not found."

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find table header and separator
    header_idx = None
    for i, line in enumerate(lines):
        if re.match(r"\|.*ID.*Title.*Description.*Category.*Risk.*Dependencies.*\|", line, re.IGNORECASE) and \
           i+1 < len(lines) and re.match(r"\|[-| ]+\|", lines[i+1]):
            header_idx = i
            break
    if header_idx is None:
        return False, "No requirements table found."

    headers = [h.strip() for h in lines[header_idx].split('|')[1:-1]]
    if attribute not in headers:
        return False, f"Attribute '{attribute}' not found in table columns. Valid columns: {headers}"

    id_col = None
    for idx, h in enumerate(headers):
        if h.lower() == "id":
            id_col = idx
            break
    if id_col is None:
        return False, "No 'ID' column found in table."

    # Find and update the row
    updated = False
    for i in range(header_idx+2, len(lines)):
        row = lines[i]
        if not row.strip().startswith("|"):
            continue
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) != len(headers):
            continue
        if cols[id_col] == req_id:
            attr_idx = headers.index(attribute)
            cols[attr_idx] = value
            lines[i] = "| " + " | ".join(cols) + " |\n"
            updated = True
            break

    if not updated:
        return False, f"Requirement with ID '{req_id}' not found."

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True, ""