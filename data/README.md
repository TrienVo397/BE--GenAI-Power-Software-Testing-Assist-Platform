# Project Data Directory

This directory contains the data for all projects. Each project has its own directory structure.

## Project Directory Structure

```
/project-<id>/
├── .git/                # Git repository
├── templates/           # Version-controlled templates
│   ├── checklist.yml    # YAML template
│   └── testcase.yml
├── artifacts/           # Current outputs
│   ├── checklist.md
│   └── testcases.md
└── versions/            # Versioned documents
    ├── v1.0/
    │   └── srs.pdf
    └── v2.0/
        └── srs.pdf
```

## Directory Descriptions

- `.git`: Git repository for version control of the entire project
- `templates`: Contains YAML templates for generating checklists and test cases
- `artifacts`: Contains the generated output files (checklists and test cases)
- `versions`: Stores versioned documents such as software requirements specifications (SRS)
