"""Test module for gac.core functionality."""

from unittest.mock import patch

import pytest

from gac.prompt import build_prompt


@patch("gac.prompt.add_repository_context", return_value="")
def test_build_prompt(mock_add_repo_context):
    """Test build_prompt function produces expected output format."""
    # Set up test inputs
    status = "On branch main"
    diff = "diff --git a/file.py b/file.py\n+New line"
    hint = "Test hint"
    one_liner = True

    # Call the function directly
    result = build_prompt(status, diff, one_liner=one_liner, hint=hint)

    # Verify the mock was called with the diff
    mock_add_repo_context.assert_called_once_with(diff)

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
        assert any(phrase in result.lower() for phrase in ["single line", "single-line"])


@patch("gac.prompt.add_repository_context", return_value="")
def test_build_prompt_without_hint(mock_add_repo_context):
    """Test build_prompt works without hint."""
    # Set up test inputs
    status = "On branch main"
    diff = "diff --git a/file.py b/file.py\n+New line"

    # Call without hint and with multi-line
    result = build_prompt(status, diff, one_liner=False)

    # Verify the mock was called with the diff
    mock_add_repo_context.assert_called_once_with(diff)

    # Check expected behavior
    assert isinstance(result, str)
    assert status in result
    assert diff in result
    # Check content relevant to multi-line format
    assert any(phrase in result.lower() for phrase in ["bullet points", "detailed body", "multiple bullet"])
