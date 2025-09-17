"""
Module to extract test case info from description in a Markdown table using semantic matching.
"""

def testcase_info_from_description(description: str, testcases_md_path: str) -> str:
    """
    Find test cases in the Markdown file that match the description (using similarity matching).
    Returns a string representation of the list of matching test cases.

    Args:
        description: The description to search for
        testcases_md_path: Path to the test cases markdown file
    
    Returns:
        String representation of a list containing matching test case dictionaries
    """
    import os
    import re
    
    if not os.path.exists(testcases_md_path):
        return "[]"  # Return empty list if file not found
    
    with open(testcases_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    # Extract Markdown table
    table_match = re.search(r"\|.*?\|\n\|[-| ]+\|\n((?:\|.*\|\n?)+)", md_text, re.DOTALL)
    if not table_match:
        return "[]"  # Return empty list if no table found
    
    table = table_match.group(0).strip().split('\n')
    headers = [h.strip() for h in table[0].split('|')[1:-1]]
    matching_cases = []
    
    # Look through each row (after header and separator)
    for row in table[2:]:
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) == len(headers):
            # Create a test case dictionary from this row
            tc_dict = dict(zip(headers, cols))
            
            # Check if any text column contains the description (case insensitive)
            # We primarily check Description and Expected Result columns if they exist
            for key in ['Description', 'ExpectedResult', 'Expected Result', 'Steps', 'Test Steps']:
                if key in tc_dict and description.lower() in tc_dict[key].lower():
                    matching_cases.append(tc_dict)
                    break
            
            # If no match in primary fields, check all other text fields
            if not any(description.lower() in tc_dict[key].lower() 
                    for key in tc_dict 
                    if key not in ['ID', 'Priority', 'Status'] and description.lower() in tc_dict[key].lower()):
                continue
    
    return str(matching_cases)
