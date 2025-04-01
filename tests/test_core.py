"""Test module for gac.core."""

import os
import unittest
from unittest.mock import MagicMock

import pytest

from gac.prompt import build_prompt


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

    def test_build_prompt_direct(self):
        """Test build_prompt function produces expected output format."""
        # Set up test inputs
        status = "On branch main"
        diff = "diff --git a/file.py b/file.py\n+New line"
        hint = "Test hint"
        one_liner = True

        # Call the function directly
        result = build_prompt(status, diff, one_liner=one_liner, hint=hint)

        # Check expected behavior: prompt contains necessary information for the LLM
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

        # Verify the prompt contains the essential components
        self.assertIn(status, result)
        self.assertIn(diff, result)
        self.assertIn(hint, result)

        # Verify one_liner flag affects the prompt content appropriately
        if one_liner:
            self.assertIn("single line", result.lower())
