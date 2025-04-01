"""Test module for gac.core functionality."""

import os

import pytest

from gac.prompt import build_prompt


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


def test_build_prompt():
    """Test build_prompt function produces expected output format."""
    # Set up test inputs
    status = "On branch main"
    diff = "diff --git a/file.py b/file.py\n+New line"
    hint = "Test hint"
    one_liner = True

    # Call the function directly
    result = build_prompt(status, diff, one_liner=one_liner, hint=hint)

    # Check expected behavior: prompt contains necessary information for the LLM
    assert isinstance(result, str)
    assert len(result) > 0

    # Verify the prompt contains the essential components
    # These are behavioral expectations, not implementation details
    assert status in result
    assert diff in result
    assert hint in result

    # Verify one_liner flag affects the prompt content appropriately
    if one_liner:
        assert "single line" in result.lower()


def test_build_prompt_without_hint():
    """Test build_prompt works without hint."""
    # Set up test inputs
    status = "On branch main"
    diff = "diff --git a/file.py b/file.py\n+New line"

    # Call without hint and with multi-line
    result = build_prompt(status, diff, one_liner=False)

    # Check expected behavior
    assert isinstance(result, str)
    assert status in result
    assert diff in result
    assert "bullet points" in result.lower()  # Multi-line should mention bullet points
