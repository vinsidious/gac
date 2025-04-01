"""Tests for gac.format module."""

from unittest.mock import patch

import pytest

from gac.format import format_files, run_formatter


@pytest.fixture
def mock_get_staged_files():
    with patch("gac.format.get_staged_files") as mock:
        yield mock


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=True)
@patch("os.path.exists", return_value=True)  # Mock os.path.exists to return True
def test_format_files_success(mock_exists, mock_check_formatter, mock_run_formatter):
    """Test format_files with successful formatting."""
    # Setup mock
    mock_run_formatter.return_value = True

    # Test with Python files
    files = ["file1.py", "file2.py"]
    result = format_files(files)

    # Verify formatter was called for Python files
    assert mock_run_formatter.call_count > 0
    assert isinstance(result, dict)

    # Reset mocks
    mock_run_formatter.reset_mock()

    # Test with multiple file types
    files = ["file1.py", "file2.js", "file3.rs", "file4.go"]
    result = format_files(files)

    # Verify formatter was called multiple times
    assert mock_run_formatter.call_count > 0
    assert isinstance(result, dict)


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=False)
@patch("os.path.exists", return_value=True)  # Mock os.path.exists to return True
def test_format_files_formatter_not_available(
    mock_exists, mock_check_formatter, mock_run_formatter
):
    """Test format_files when formatter is not available."""
    files = ["file1.py", "file2.py"]
    result = format_files(files)

    # Formatter should not be called if not available
    mock_run_formatter.assert_not_called()
    assert isinstance(result, dict)


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=True)
def test_format_files_no_files(mock_check_formatter, mock_run_formatter):
    """Test format_files with no files."""
    result = format_files([])

    # Should return empty dict when no files
    assert result == {}
    mock_run_formatter.assert_not_called()


@patch("gac.format.subprocess.run")
def test_run_formatter_success(mock_subprocess_run):
    """Test run_formatter with successful execution."""
    # Setup mock
    mock_subprocess_run.return_value.returncode = 0

    # Test
    result = run_formatter(["black"], ["file1.py", "file2.py"], "black")

    # Verify
    assert result is True
    mock_subprocess_run.assert_called_once()


@patch("gac.format.subprocess.run")
def test_run_formatter_failure(mock_subprocess_run):
    """Test run_formatter with command failure."""
    # Setup mock
    mock_subprocess_run.return_value.returncode = 1
    mock_subprocess_run.return_value.stderr = "Error message"

    # Test
    result = run_formatter(["black"], ["file1.py", "file2.py"], "black")

    # Verify
    assert result is False
    mock_subprocess_run.assert_called_once()


@patch("gac.format.subprocess.run")
def test_run_formatter_exception(mock_subprocess_run):
    """Test run_formatter with exception."""
    # Setup mock
    mock_subprocess_run.side_effect = Exception("Command failed")

    # Test
    result = run_formatter(["black"], ["file1.py", "file2.py"], "black")

    # Verify
    assert result is False
    mock_subprocess_run.assert_called_once()


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=True)
@patch("os.path.exists", return_value=True)  # Mock os.path.exists to return True
def test_format_files_with_dict_input(mock_exists, mock_check_formatter, mock_run_formatter):
    """Test format_files with dictionary input (backward compatibility)."""
    # Setup mock
    mock_run_formatter.return_value = True

    # Test with dict input (path -> status)
    files = {"file1.py": "M", "file2.py": "A", "deleted.py": "D"}  # Should be skipped

    result = format_files(files)

    # Verify formatter was called
    assert mock_run_formatter.call_count > 0
    assert isinstance(result, dict)

    # Ensure deleted files were skipped
    for call_args in mock_run_formatter.call_args_list:
        files_arg = call_args[0][1]  # Second positional arg is files list
        assert "deleted.py" not in files_arg
