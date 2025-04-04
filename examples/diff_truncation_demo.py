#!/usr/bin/env python3
"""
Demo script for semantic-aware diff truncation.

This script demonstrates how the enhanced diff truncation works
by comparing the original implementation with the new semantic-aware
version on a real-world diff.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import gac
sys.path.insert(0, str(Path(__file__).parent.parent))
from gac.ai import count_tokens, truncate_git_diff  # noqa: E402

# Simple example diff
EXAMPLE_DIFF = """diff --git a/src/core.py b/src/core.py
index 123abc..456def 100644
--- a/src/core.py
+++ b/src/core.py
@@ -10,7 +10,8 @@ class CoreProcessor:
     def process_data(self, data):
         # Process the input data
-        return data.transform()
+        # Apply validation before transformation
+        return data.validate().transform()

diff --git a/src/utils.py b/src/utils.py
index 789xyz..abc123 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -5,3 +5,6 @@ def helper_function(x):
     # Helper utility function
     return x * 2

+def format_output(result):
+    # Format the output for display
+    return "Result: " + str(result)"""


def main():
    """Demonstrate the enhanced diff truncation."""
    print("Demonstrating semantic-aware diff truncation")
    print("=" * 50)

    # Calculate token count for the original diff
    model = "anthropic:claude-3-5-haiku-latest"
    token_count = count_tokens(EXAMPLE_DIFF, model)
    print(f"Original diff token count: {token_count}")

    # Set a small token limit to force truncation
    token_limit = token_count // 2
    print(f"Using token limit of {token_limit} (50% of original)")

    # Truncate with the enhanced implementation
    truncated_diff = truncate_git_diff(EXAMPLE_DIFF, model, token_limit)
    truncated_token_count = count_tokens(truncated_diff, model)

    # Display results
    print("\nTruncated diff:")
    print("-" * 50)
    print(truncated_diff)
    print("-" * 50)
    print(f"Truncated diff token count: {truncated_token_count}")
    print(f"Reduction: {100 - (truncated_token_count / token_count) * 100:.1f}%")

    # Explain semantic preservation
    print("\nSemantic content preserved:")
    semantic_features = ["CoreProcessor", "process_data", "format_output"]

    for feature in semantic_features:
        if feature.lower() in truncated_diff.lower():
            print(f"✓ {feature}")
        else:
            print(f"✗ {feature}")


if __name__ == "__main__":
    main()
