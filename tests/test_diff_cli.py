from unittest.mock import patch

import pytest

from gac.diff_cli import _diff_implementation
from gac.errors import GitError


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="filtered diff")
@patch("gac.diff_cli.smart_truncate_diff", return_value="truncated diff")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_with_commits(mock_get_diff, mock_staged_files, mock_truncate, mock_filter, mock_print, mock_exit):
    """Test that get_diff is called with two commit parameters."""
    mock_get_diff.return_value = "Test diff output"

    # Test with two commits
    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=True, max_tokens=None, staged=True, color=True, commit1="abc123", commit2="def456"
        )

    # Assert get_diff was called with the expected parameters
    mock_get_diff.assert_called_once_with(staged=True, color=True, commit1="abc123", commit2="def456")


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="filtered diff")
@patch("gac.diff_cli.smart_truncate_diff", return_value="truncated diff")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_with_single_commit(mock_get_diff, mock_staged_files, mock_truncate, mock_filter, mock_print, mock_exit):
    """Test that get_diff is called with one commit parameter."""
    mock_get_diff.return_value = "Test diff output"

    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=True, max_tokens=None, staged=True, color=True, commit1="abc123", commit2=None
        )

    # Assert get_diff was called with the expected parameters
    mock_get_diff.assert_called_once_with(staged=True, color=True, commit1="abc123", commit2=None)


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="filtered diff")
@patch("gac.diff_cli.smart_truncate_diff", return_value="truncated diff")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_with_branch_names(mock_get_diff, mock_staged_files, mock_truncate, mock_filter, mock_print, mock_exit):
    """Test that get_diff is called with branch names."""
    mock_get_diff.return_value = "Test diff output"

    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True,
            truncate=True,
            max_tokens=None,
            staged=True,
            color=True,
            commit1="main",
            commit2="feature/branch",
        )

    # Assert get_diff was called with the expected parameters
    mock_get_diff.assert_called_once_with(staged=True, color=True, commit1="main", commit2="feature/branch")


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="filtered diff")
@patch("gac.diff_cli.smart_truncate_diff", return_value="truncated diff")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_with_unstaged(mock_get_diff, mock_staged_files, mock_truncate, mock_filter, mock_print, mock_exit):
    """Test that get_diff is called with unstaged parameter."""
    mock_get_diff.return_value = "Test diff output"

    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=True, max_tokens=None, staged=False, color=True, commit1=None, commit2=None
        )

    # Assert get_diff was called with the expected parameters
    mock_get_diff.assert_called_once_with(staged=False, color=True, commit1=None, commit2=None)


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print_message")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="filtered diff")
@patch("gac.diff_cli.smart_truncate_diff", return_value="truncated diff")
@patch("gac.diff_cli.get_diff", return_value="test diff")
@patch("gac.diff_cli.get_staged_files", return_value=[])
def test_no_staged_files_produces_error(
    mock_staged_files, mock_get_diff, mock_truncate, mock_filter, mock_print_message, mock_exit
):
    """Test that an error is shown when there are no staged files."""
    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=True, max_tokens=None, staged=True, color=True, commit1=None, commit2=None
        )

    # Assert error message was shown
    mock_print_message.assert_called_once_with(
        "No staged changes found. Use 'git add' to stage changes.", level="error"
    )
    mock_exit.assert_called_once_with(1)


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print_message")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="filtered diff")
@patch("gac.diff_cli.smart_truncate_diff", return_value="truncated diff")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff", return_value="")
def test_empty_diff_produces_error(
    mock_get_diff, mock_staged_files, mock_truncate, mock_filter, mock_print_message, mock_exit
):
    """Test that an error is shown when the diff is empty."""
    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=True, max_tokens=None, staged=True, color=True, commit1=None, commit2=None
        )

    # Assert error message was shown
    mock_print_message.assert_called_once_with("No changes to display.", level="error")
    mock_exit.assert_called_once_with(1)


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print")
@patch("gac.diff_cli.filter_binary_and_minified")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_no_color_strips_ansi(mock_get_diff, mock_staged_files, mock_filter, mock_print, mock_exit):
    """Test that ANSI color codes are stripped when color is disabled."""
    # Diff with ANSI color codes
    colored_diff = "\x1b[32m+added line\x1b[0m\n\x1b[31m-removed line\x1b[0m"
    mock_get_diff.return_value = colored_diff
    # Make filter return the same content (filtering is separate concern)
    mock_filter.return_value = colored_diff

    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=False, max_tokens=None, staged=True, color=False, commit1=None, commit2=None
        )

    # Assert print was called with ANSI codes stripped
    printed_output = mock_print.call_args[0][0]
    assert "\x1b[" not in printed_output
    assert "+added line" in printed_output
    assert "-removed line" in printed_output


@patch("gac.diff_cli.print_message")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_git_error_handling(mock_get_diff, mock_staged_files, mock_print_message):
    """Test that GitError is properly handled."""
    mock_get_diff.side_effect = GitError("Git command failed")

    with patch("gac.diff_cli.setup_logging"):
        with pytest.raises(SystemExit) as exc_info:
            _diff_implementation(
                filter=True, truncate=True, max_tokens=None, staged=True, color=True, commit1=None, commit2=None
            )

    # Assert error message was shown and exit code is 1
    mock_print_message.assert_called_once_with("Error getting diff: Git command failed", level="error")
    assert exc_info.value.code == 1


@patch("gac.diff_cli.sys.exit")
@patch("gac.diff_cli.print_message")
@patch("gac.diff_cli.filter_binary_and_minified", return_value="")
@patch("gac.diff_cli.get_staged_files", return_value=["file1.py"])
@patch("gac.diff_cli.get_diff")
def test_diff_empty_after_filtering(mock_get_diff, mock_staged_files, mock_filter, mock_print_message, mock_exit):
    """Test that error is shown when diff is empty after filtering."""
    mock_get_diff.return_value = "diff with binary files"

    with patch("gac.diff_cli.setup_logging"):
        _diff_implementation(
            filter=True, truncate=True, max_tokens=None, staged=True, color=True, commit1=None, commit2=None
        )

    # Assert error message was shown
    mock_print_message.assert_called_once_with("No changes to display after filtering.", level="error")
    mock_exit.assert_called_once_with(1)
