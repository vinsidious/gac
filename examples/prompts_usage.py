#!/usr/bin/env python3
"""
Example demonstrating how to use the gac prompts module.

This file shows how to:
1. Build prompts for LLMs to generate commit messages
2. Clean commit messages from LLM responses
3. Create abbreviated versions of prompts
"""

import os
import sys

# Add the src directory to the path so we can import gac modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from gac.prompts import build_prompt, clean_commit_message, create_abbreviated_prompt


def example_build_prompt():
    """Demonstrate how to build various types of prompts."""
    # Example git status and diff
    status = """On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   src/gac/core.py
        new file:   src/gac/prompts.py
"""

    diff = """diff --git a/src/gac/core.py b/src/gac/core.py
index abcdefg..1234567 100644
--- a/src/gac/core.py
+++ b/src/gac/core.py
@@ -25,7 +25,7 @@ from gac.git import (
     get_staged_files,
     stage_files,
 )
+from gac.prompts import build_prompt, clean_commit_message, create_abbreviated_prompt
 from gac.utils import (
     print_error,
     print_header,
diff --git a/src/gac/prompts.py b/src/gac/prompts.py
new file mode 100644
index 0000000..fedcba9
--- /dev/null
+++ b/src/gac/prompts.py
@@ -0,0 +1,232 @@
+\"\"\"Module for prompt-related functionality for gac.\"\"\"
+
+def build_prompt(
+    status: str, diff: str, one_liner: bool = False, hint: str = "", conventional: bool = False
+) -> str:
"""

    print("Example 1: Basic prompt")
    print("-----------------------")
    prompt = build_prompt(status, diff)
    print(f"Length: {len(prompt)} characters")
    print(f"First 150 characters: {prompt[:150]}...\n")

    print("Example 2: One-liner prompt")
    print("--------------------------")
    prompt = build_prompt(status, diff, one_liner=True)
    print(f"Contains 'single line' instruction: {'single line' in prompt}")
    print(f"First 150 characters: {prompt[:150]}...\n")

    print("Example 3: Conventional commit prompt")
    print("------------------------------------")
    prompt = build_prompt(status, diff, conventional=True)
    print(f"Contains conventional prefix instructions: {'conventional commit prefix' in prompt}")
    print(f"First 150 characters: {prompt[:150]}...\n")

    print("Example 4: Prompt with hint")
    print("--------------------------")
    prompt = build_prompt(status, diff, hint="JIRA-123: Refactor prompt handling")
    print(f"Contains hint: {'JIRA-123' in prompt}")
    print(f"First 150 characters: {prompt[:150]}...\n")

    # Return a prompt for the next examples
    return build_prompt(status, diff)


def example_clean_commit_message():
    """Demonstrate how to clean commit messages."""
    print("Example 1: Cleaning backticks")
    print("-----------------------------")
    message = """```
feat: Add new prompt module

- Refactored prompt handling from core.py
- Added tests for new functionality
```"""
    cleaned = clean_commit_message(message)
    print(f"Original: {message}")
    print(f"Cleaned: {cleaned}\n")

    print("Example 2: Adding conventional prefix")
    print("------------------------------------")
    message = """Refactor prompt handling
    
- Move prompt-related code to a new module
- Add comprehensive tests
"""
    cleaned = clean_commit_message(message)
    print(f"Original: {message}")
    print(f"Cleaned: {cleaned}\n")

    print("Example 3: Cleaning code blocks with language")
    print("-------------------------------------------")
    message = """```python
def example():
    print("This is an example")
```"""
    cleaned = clean_commit_message(message)
    print(f"Original: {message}")
    print(f"Cleaned: {cleaned}\n")

    print("Example 4: Cleaning XML tags and bullet points")
    print("--------------------------------------------")
    message = """<git-status>
On branch main
</git-status>

refactor: Improve prompt handling

- <git-diff>diff content</git-diff> Extract prompt builder
- Add dedicated module for prompts
"""
    cleaned = clean_commit_message(message)
    print(f"Original: {message}")
    print(f"Cleaned: {cleaned}\n")


def example_abbreviate_prompt():
    """Demonstrate how to abbreviate prompts."""
    # Create a long diff
    status = "M file1.py\nA file2.py"
    diff_lines = [f"Line {i} of diff content" for i in range(200)]
    diff = "\n".join(diff_lines)

    # Build the full prompt
    full_prompt = build_prompt(status, diff)

    print("Full prompt information")
    print("-----------------------")
    print(f"Length: {len(full_prompt)} characters")
    print(f"Number of lines: {full_prompt.count(chr(10)) + 1}\n")

    # Create abbreviated versions with different settings
    print("Example 1: Default abbreviation (50 lines)")
    print("------------------------------------------")
    abbrev_default = create_abbreviated_prompt(full_prompt)
    print(f"Length: {len(abbrev_default)} characters")
    print(f"Number of lines: {abbrev_default.count(chr(10)) + 1}")
    print(f"Contains hidden message: {'lines hidden' in abbrev_default}\n")

    print("Example 2: Custom line limit (20 lines)")
    print("--------------------------------------")
    abbrev_custom = create_abbreviated_prompt(full_prompt, max_diff_lines=20)
    print(f"Length: {len(abbrev_custom)} characters")
    print(f"Number of lines: {abbrev_custom.count(chr(10)) + 1}")
    print(f"Contains hidden message: {'lines hidden' in abbrev_custom}\n")

    # Create a short diff to demonstrate no abbreviation
    short_diff = "\n".join(diff_lines[:10])
    short_prompt = build_prompt(status, short_diff)

    print("Example 3: Short prompt (no abbreviation)")
    print("----------------------------------------")
    abbrev_short = create_abbreviated_prompt(short_prompt, max_diff_lines=20)
    print(f"Length: {len(abbrev_short)} characters")
    print(f"Is identical to original: {abbrev_short == short_prompt}")
    print(f"Contains hidden message: {'lines hidden' in abbrev_short}\n")


if __name__ == "__main__":
    print("GAC Prompts Module Usage Examples")
    print("================================\n")

    print("PART 1: BUILDING PROMPTS")
    print("======================\n")
    prompt = example_build_prompt()

    print("\nPART 2: CLEANING COMMIT MESSAGES")
    print("==============================\n")
    example_clean_commit_message()

    print("\nPART 3: ABBREVIATING PROMPTS")
    print("==========================\n")
    example_abbreviate_prompt()
