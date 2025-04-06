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
@patch("os.path.isfile", return_value=True)
@patch("os.path.exists", return_value=True)
def test_format_files_success(mock_exists, mock_isfile, mock_check_formatter, mock_run_formatter):
    """Test format_files successfully formats different file types."""
    # Setup mock to simulate successful formatting
    mock_run_formatter.return_value = True

    # Test with Python files (update to dictionary)
    files = {"file1.py": "M", "file2.py": "M"}
    result = format_files(files)

    # Verify the behavior: function returns a list of formatted files
    assert isinstance(result, list)
    assert "file1.py" in result
    assert "file2.py" in result

    # Reset mocks for next test
    mock_run_formatter.reset_mock()

    # Test with multiple file types (update to dictionary)
    files = {"file1.py": "M", "file2.js": "M", "file3.rs": "M", "file4.go": "M"}
    result = format_files(files)

    # Verify the behavior: function returns a list with all formatted files
    assert isinstance(result, list)
    assert "file1.py" in result
    assert "file2.js" in result
    assert "file3.rs" in result
    assert "file4.go" in result


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=False)
@patch("os.path.isfile", return_value=True)
@patch("os.path.exists", return_value=True)
def test_format_files_formatter_not_available(mock_exists, mock_isfile, mock_check_formatter, mock_run_formatter):
    """Test format_files handles unavailable formatters gracefully."""
    # Test with files that would normally be formatted (update to dictionary)
    files = {"file1.py": "M", "file2.py": "M"}
    result = format_files(files)

    # Verify the behavior: function returns an empty list when no formatters are available
    assert isinstance(result, list)
    assert not result

    # Verify no formatting was attempted when formatter is unavailable
    mock_run_formatter.assert_not_called()


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=True)
def test_format_files_no_files(mock_check_formatter, mock_run_formatter):
    """Test format_files handles empty file list appropriately."""
    # Test with empty file list (update to empty dictionary)
    result = format_files({})

    # Verify the behavior: function returns an empty list
    assert result == []

    # Verify no formatting was attempted with empty file list
    mock_run_formatter.assert_not_called()


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


@patch("gac.format.run_formatter")
@patch("gac.format.check_formatter_available", return_value=True)
@patch("os.path.isfile", return_value=True)
@patch("os.path.exists", return_value=True)
def test_format_files_with_dict_input(mock_exists, mock_isfile, mock_check_formatter, mock_run_formatter):
    """Test format_files handles dictionary input correctly."""
    # Setup mock to simulate successful formatting
    mock_run_formatter.return_value = True

    # Test with dictionary input (path -> status)
    files = {"file1.py": "M", "file2.py": "A"}

    # Call the function
    result = format_files(files)

    # Verify the behavior: function returns a list of formatted files
    assert isinstance(result, list)

    # Verify all files are included in the result
    assert "file1.py" in result
    assert "file2.py" in result
