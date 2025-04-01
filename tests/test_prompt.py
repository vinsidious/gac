"""Tests for prompt-related functionality."""

import unittest

from gac.prompt import build_prompt, clean_commit_message, create_abbreviated_prompt


class TestPrompts(unittest.TestCase):
    """Tests for prompt-related functions."""

    def test_build_prompt(self):
        """Test build_prompt builds prompts correctly."""
        # Test basic prompt
        status = "M file1.py"
        diff = "diff --git a/file1.py b/file1.py"
        result = build_prompt(status, diff)

        # Check structure
        self.assertIn("Write a concise and meaningful git commit message", result)
        self.assertIn("<git-status>", result)
        self.assertIn(status, result)
        self.assertIn("</git-status>", result)
        self.assertIn("<git-diff>", result)
        self.assertIn(diff, result)
        self.assertIn("</git-diff>", result)

        # Test one-liner option
        result = build_prompt(status, diff, one_liner=True)
        self.assertIn("Format it as a single line", result)

        # Test conventional format is always included
        result = build_prompt(status, diff)
        self.assertIn(
            "IMPORTANT: EVERY commit message MUST start with a conventional commit prefix", result
        )
        self.assertIn("feat:", result)
        self.assertIn("fix:", result)

        # Test hint option
        hint = "JIRA-123"
        result = build_prompt(status, diff, hint=hint)
        self.assertIn(f"Please consider this context from the user: {hint}", result)

        # Test combinations
        result = build_prompt(status, diff, one_liner=True, hint=hint)
        self.assertIn("Format it as a single line", result)
        self.assertIn(
            "IMPORTANT: EVERY commit message MUST start with a conventional commit prefix", result
        )
        self.assertIn(f"Please consider this context from the user: {hint}", result)

    def test_clean_commit_message(self):
        """Test clean_commit_message cleans messages correctly."""
        # Test cleaning backticks
        message = "```\nTest message\n```"
        result = clean_commit_message(message)
        self.assertEqual(result, "chore: Test message")

        # Test adding conventional commit prefix
        message = "Test message"
        result = clean_commit_message(message)
        self.assertEqual(result, "chore: Test message")

        # Test preserving existing conventional commit prefix
        message = "feat: Added new feature"
        result = clean_commit_message(message)
        self.assertEqual(result, "feat: Added new feature")

    def test_create_abbreviated_prompt(self):
        """Test create_abbreviated_prompt shortens prompts correctly."""
        # Create a long diff prompt
        status = "M file1.py"
        lines = [f"Line {i}" for i in range(100)]
        diff = "\n".join(lines)
        prompt = build_prompt(status, diff)

        # Test abbreviation
        result = create_abbreviated_prompt(prompt, max_diff_lines=20)
        self.assertIn("lines hidden", result)
        self.assertIn("Use --show-prompt-full", result)

        # Test short diff not abbreviated
        short_diff = "\n".join([f"Line {i}" for i in range(10)])
        short_prompt = build_prompt(status, short_diff)
        result = create_abbreviated_prompt(short_prompt, max_diff_lines=20)
        self.assertEqual(result, short_prompt)

        # Test edge cases
        # No markers found
        no_marker_prompt = "This is a prompt without markers"
        result = create_abbreviated_prompt(no_marker_prompt)
        self.assertEqual(result, no_marker_prompt)

        # No git-diff tag
        no_diff_prompt = "Changes to be committed:\nNo diff tag"
        result = create_abbreviated_prompt(no_diff_prompt)
        self.assertEqual(result, no_diff_prompt)

        # No closing git-diff tag
        no_close_prompt = "Changes to be committed:\n<git-diff>\nNo closing tag"
        result = create_abbreviated_prompt(no_close_prompt)
        self.assertEqual(result, no_close_prompt)


if __name__ == "__main__":
    unittest.main()
