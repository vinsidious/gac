# GAC Prompts Module

The `prompts` module contains functionality for building, cleaning, and managing prompts used to generate commit messages with large language models.

## Overview

This module was created as part of the codebase refactoring to reduce the monolithic nature of the `core.py` file. It extracts all prompt-related functionality into a dedicated module with clear responsibilities.

## Functions

### `build_prompt(status, diff, one_liner=False, hint="", conventional=False)`

Builds a prompt for the LLM to generate a commit message based on git status and diff information.

**Parameters:**

- `status` (str): Output of `git status`
- `diff` (str): Output of `git diff --staged`  
- `one_liner` (bool): If True, request a single-line commit message
- `hint` (str): Optional context to include in the prompt (like "JIRA-123")
- `conventional` (bool): If True, request a conventional commit format message

**Returns:**

- A formatted prompt string

**Example:**

```python
from gac.prompts import build_prompt

# Get git status and diff (typically from git commands)
status = "M file1.py\nA file2.py"
diff = "diff --git a/file1.py b/file1.py\n..."

# Build a basic prompt
prompt = build_prompt(status, diff)

# Build a prompt for a one-liner conventional commit with hint
prompt = build_prompt(
    status, 
    diff, 
    one_liner=True, 
    hint="JIRA-123", 
    conventional=True
)
```

### `clean_commit_message(message)`

Cleans a commit message returned from an LLM to ensure it doesn't contain triple backticks, XML tags, and enforces conventional commit prefixes.

**Parameters:**

- `message` (str): The commit message to clean

**Returns:**

- The cleaned commit message

**Example:**

```python
from gac.prompts import clean_commit_message

# Clean a message with backticks (common in LLM responses)
message = """```
Add new feature

- Implemented X functionality
- Fixed Y bug
```"""

cleaned = clean_commit_message(message)
# Result: "chore: Add new feature\n\n- Implemented X functionality\n- Fixed Y bug"
```

### `create_abbreviated_prompt(prompt, max_diff_lines=50)`

Creates an abbreviated version of the prompt by limiting the diff lines to reduce token count.

**Parameters:**

- `prompt` (str): The original full prompt
- `max_diff_lines` (int): Maximum number of diff lines to include

**Returns:**

- Abbreviated prompt with a note about hidden lines

**Example:**

```python
from gac.prompts import build_prompt, create_abbreviated_prompt

# Create a prompt with a long diff
status = "M file1.py"
diff = "..." # Long diff with many lines
full_prompt = build_prompt(status, diff)

# Create an abbreviated version
abbreviated = create_abbreviated_prompt(full_prompt, max_diff_lines=30)
```

## Usage Tips

1. **When to use `build_prompt`**:
   - Use when you need to construct a prompt for an LLM based on git information
   - Customize the prompt type based on your needs (one-liner, conventional, etc.)

2. **When to use `clean_commit_message`**:
   - Always use this on responses from LLMs to ensure proper formatting
   - It handles common issues like backticks, language identifiers, and XML tags
   - It enforces conventional commit format by adding "chore: " prefix if needed

3. **When to use `create_abbreviated_prompt`**:
   - Use when you want to display a prompt to the user without showing the entire diff
   - Useful for keeping console output manageable
   - Helps to reduce visual noise while still showing enough context

## Complete Example

```python
from gac.git import get_staged_diff, get_staged_files
from gac.prompts import build_prompt, clean_commit_message, create_abbreviated_prompt
from gac.ai_utils import chat

# Get git information
status = run_subprocess(["git", "status"])
diff, _ = get_staged_diff()

# Build prompt
prompt = build_prompt(status, diff, conventional=True)

# Show abbreviated prompt to user (optional)
print(create_abbreviated_prompt(prompt))

# Send to LLM
messages = [{"role": "user", "content": prompt}]
response = chat(messages=messages, model="anthropic:claude-3-haiku")

# Clean and use commit message
commit_message = clean_commit_message(response)
print(f"Generated commit message:\n{commit_message}")

# Use the commit message (e.g., run git commit)
```

## Implementation Details

- The module handles the complexities of formatting prompts for different LLM providers
- It uses XML-like tags to structure the prompt (`<git-status>`, `<git-diff>`)
- The cleaning function is robust to different LLM outputs, handling various edge cases
- Prompts include carefully crafted instructions to guide the LLM
