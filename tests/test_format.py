"""Tests for gac.format module."""

from unittest.mock import patch

from gac.format import run_formatter


@patch("gac.format.subprocess.run")
def test_run_formatter_success(mock_subprocess_run):
    """Test run_formatter returns True when formatting succeeds."""
    # Setup mock to simulate successful command execution
    mock_subprocess_run.return_value.returncode = 0

    # Test formatting files
    result = run_formatter(["black"], ["file1.py", "file2.py"], "black")

    # Verify the behavior: function returns True on success
    assert result is True


@patch("gac.format.subprocess.run")
def test_run_formatter_failure(mock_subprocess_run):
    """Test run_formatter returns False when formatting fails."""
    # Setup mock to simulate command failure
    mock_subprocess_run.return_value.returncode = 1
    mock_subprocess_run.return_value.stderr = "Error message"

    # Test formatting files
    result = run_formatter(["black"], ["file1.py", "file2.py"], "black")

    # Verify the behavior: function returns False on failure
    assert result is False


@patch("gac.format.subprocess.run")
def test_run_formatter_exception(mock_subprocess_run):
    """Test run_formatter handles exceptions gracefully."""
    # Setup mock to simulate exception during command execution
    mock_subprocess_run.side_effect = Exception("Command failed")

    # Test formatting files
    result = run_formatter(["black"], ["file1.py", "file2.py"], "black")

    # Verify the behavior: function returns False on exception
    assert result is False
