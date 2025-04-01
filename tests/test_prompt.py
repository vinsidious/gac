"""Tests for prompt-related functionality."""

import unittest

from gac.prompt import build_prompt, clean_commit_message, create_abbreviated_prompt


class TestPrompts(unittest.TestCase):
    """Tests for prompt-related functions."""

    def test_build_prompt(self):
        """Test build_prompt creates prompts with expected content based on inputs."""
        # Test basic prompt
        status = "M file1.py"
        diff = "diff --git a/file1.py b/file1.py"
        result = build_prompt(status, diff)

        # Verify the behavior: prompt contains the necessary information
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertIn(status, result)
        self.assertIn(diff, result)

        # Test one-liner option behavior
        result_one_liner = build_prompt(status, diff, one_liner=True)
        self.assertIn("single line", result_one_liner.lower())

        # Test hint option behavior
        hint = "JIRA-123"
        result_with_hint = build_prompt(status, diff, hint=hint)
        self.assertIn(hint, result_with_hint)

        # Test combinations of options
        result_combined = build_prompt(status, diff, one_liner=True, hint=hint)
        self.assertIn("single line", result_combined.lower())
        self.assertIn(hint, result_combined)

    def test_clean_commit_message(self):
        """Test clean_commit_message properly formats commit messages."""
        # Test cleaning backticks
        message = "```\nTest message\n```"
        result = clean_commit_message(message)
        self.assertEqual(result, "chore: Test message")

        # Test adding conventional commit prefix when missing
        message = "Test message"
        result = clean_commit_message(message)
        self.assertEqual(result, "chore: Test message")

        # Test preserving existing conventional commit prefix
        message = "feat: Added new feature"
        result = clean_commit_message(message)
        self.assertEqual(result, "feat: Added new feature")

    def test_create_abbreviated_prompt(self):
        """Test create_abbreviated_prompt shortens long prompts while preserving key information."""
        # Create a long diff prompt
        status = "M file1.py"
        lines = [f"Line {i}" for i in range(10000)]
        diff = "\n".join(lines)

        # Ensure we have a prompt with the diff tags and content
        prompt = f"""
Git status:
<git-status>
{status}
</git-status>

Changes to be committed:
<git-diff>
{diff}
</git-diff>
"""

        # Test abbreviation behavior with long diff
        max_diff_lines = 20
        result = create_abbreviated_prompt(prompt, max_diff_lines=max_diff_lines)

        # Verify the behavior: long prompts are shortened
        self.assertLess(len(result), len(prompt))

        # Count the number of diff lines in the abbreviated prompt
        diff_start = result.find("<git-diff>")
        diff_end = result.find("</git-diff>")
        if diff_start != -1 and diff_end != -1:
            diff_content = result[diff_start:diff_end]
            diff_lines = diff_content.count("\n")
            # The number of diff lines should be less than or equal to max_diff_lines
            # plus some overhead for the hidden lines message
            self.assertLessEqual(diff_lines, max_diff_lines + 5)

        # Test behavior with short diff
        short_diff = "\n".join([f"Line {i}" for i in range(10)])
        short_prompt = build_prompt(status, short_diff)
        result_short = create_abbreviated_prompt(short_prompt, max_diff_lines=20)

        # Verify the behavior: short prompts are not abbreviated
        self.assertEqual(result_short, short_prompt)

        # Test edge case behaviors
        # No markers found
        no_marker_prompt = "This is a prompt without markers"
        result_no_marker = create_abbreviated_prompt(no_marker_prompt)
        self.assertEqual(result_no_marker, no_marker_prompt)

        # No git-diff tag
        no_diff_prompt = "Changes to be committed:\nNo diff tag"
        result_no_diff = create_abbreviated_prompt(no_diff_prompt)
        self.assertEqual(result_no_diff, no_diff_prompt)


if __name__ == "__main__":
    unittest.main()
