"""Test module for gac.core functionality."""

from gac.prompt import build_prompt


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
        assert "<one_liner>" in result
        assert "<multi_line>" not in result
    else:
        assert "<one_liner>" not in result
        assert "<multi_line>" in result


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
    # Check content relevant to multi-line format
    assert "<multi_line>" in result
    assert "<one_liner>" not in result
