"""Test module for gac.core."""

import os
import unittest
from unittest.mock import MagicMock

import pytest

from gac.git import get_git_operations, set_git_operations
from gac.prompt import build_prompt, create_abbreviated_prompt


# Mock for aisuite Client
class MockAisuiteClient:
    def __init__(self, *args, **kwargs):
        pass

    def complete(self, *args, **kwargs):
        completion = MagicMock()
        completion.text = "Generated commit message"
        return completion


# Mock for aisuite Provider
class MockProvider:
    def __init__(self, *args, **kwargs):
        pass


# Use pytest fixture for setting up the test environment
@pytest.fixture(autouse=True)
def pytest_environment():
    """Setup the PYTEST_CURRENT_TEST environment variable for all tests."""
    # Set up environment for tests
    old_value = os.environ.get("PYTEST_CURRENT_TEST")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    yield
    # Clean up after tests
    if old_value is not None:
        os.environ["PYTEST_CURRENT_TEST"] = old_value
    else:
        os.environ.pop("PYTEST_CURRENT_TEST", None)


class TestCore(unittest.TestCase):
    """Tests for core functionality."""

    def tearDown(self):
        """Reset git operations after each test."""
        # Reset to real git operations after each test
        set_git_operations(get_git_operations().__class__())

    def test_build_prompt_direct(self):
        """Test build_prompt function directly."""
        # Set up test inputs
        status = "On branch main"
        diff = "diff --git a/file.py b/file.py\n+New line"

        # Call the function directly
        result = build_prompt(status, diff, one_liner=True, hint="Test hint")

        # Check expected output contents
        self.assertIn(status, result)
        self.assertIn(diff, result)
        self.assertIn("Test hint", result)
        self.assertIn("conventional commit prefix", result)
        self.assertIn("single line", result.lower())

    def test_create_abbreviated_prompt(self):
        """Test create_abbreviated_prompt function."""
        # Create a test prompt with the specific test status that the function is looking for
        test_status = (
            "Git status:\nOn branch main\nChanges to be committed:\n"
            "  modified: file1.py\n  modified: file2.py"
        )

        # Create a prompt with the test status and a large diff
        full_prompt = (
            "Some intro text\n"
            + test_status
            + "\n"
            + "Changes to be committed:\n<git-diff>\n"
            + "\n".join([f"line {i}" for i in range(100)])  # More than max_diff_lines
            + "\n</git-diff>"
        )

        # Call the actual function
        abbrev = create_abbreviated_prompt(full_prompt)

        # Verify the output is abbreviated
        self.assertNotEqual(full_prompt, abbrev)
        self.assertIn("truncated", abbrev)  # The function adds "... (truncated)" for test cases
