"""
Module to change a test case attribute in a Markdown table by ID.
"""
def change_testcase_info(testcases_md_path: str, tc_id: str, attribute: str, value: str):
    """
    Change the attribute of a test case in the Markdown file by ID.
    Returns (True, msg) if successful, (False, error_msg) otherwise.
    """
    import os
    import re
    if not os.path.exists(testcases_md_path):
        return False, "Test cases file not found."
    
    with open(testcases_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    table_match = re.search(r"\|.*?\|\n\|[-| ]+\|\n((?:\|.*\|\n?)+)", md_text, re.DOTALL)
    if not table_match:
        return False, "No test cases table found."
    
    table = table_match.group(0).strip().split('\n')
    headers = [h.strip() for h in table[0].split('|')[1:-1]]
    
    if attribute not in headers:
        return False, f"Attribute '{attribute}' not found in test cases table."
    
    id_col = None
    for i, h in enumerate(headers):
        if h.lower() == "id":
            id_col = i
            break
    if id_col is None:
        return False, "No 'ID' column found in test cases table."
    
    changed = False
    for idx, row in enumerate(table[2:]):  # skip header and separator
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) == len(headers) and cols[id_col] == tc_id:
            col_idx = headers.index(attribute)
            cols[col_idx] = value
            table[idx+2] = '| ' + ' | '.join(cols) + ' |'
            changed = True
            break
    
    if not changed:
        return False, f"Test case with ID '{tc_id}' not found."
    
    # Replace table in md_text
    new_table = '\n'.join(table)
    new_md_text = md_text.replace(table_match.group(0), new_table)
    with open(testcases_md_path, "w", encoding="utf-8") as f:
        f.write(new_md_text)
    
    return True, "Test case updated successfully."
