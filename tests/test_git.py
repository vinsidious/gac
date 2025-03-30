"""Test module for gac.git."""

import subprocess
import unittest
from unittest.mock import mock_open, patch

from gac.git import (
    FileStatus,
    commit_changes,
    get_file_diff,
    get_project_description,
    get_staged_diff,
    get_staged_files,
    is_large_file,
    stage_files,
)


class TestGit(unittest.TestCase):
    """Tests for git functions."""

    @patch("gac.git.run_subprocess")
    def test_get_staged_files(self, mock_run_subprocess):
        """Test get_staged_files returns correct result."""
        # Mock run_subprocess to return staged files with git status -s format
        mock_run_subprocess.return_value = "M file1.py\nM file2.md\nM file3.js\n?? unstaged.txt"

        # Call get_staged_files
        result = get_staged_files()

        # Assert mock was called correctly with git status -s
        mock_run_subprocess.assert_called_once_with(["git", "status", "-s"])

        # Assert result is list of files
        self.assertEqual(result, ["file1.py", "file2.md", "file3.js"])

    @patch("gac.git.run_subprocess")
    def test_get_staged_files_with_type(self, mock_run_subprocess):
        """Test get_staged_files with file_type filter returns correct result."""
        # Mock run_subprocess to return staged files with git status -s format
        mock_run_subprocess.return_value = (
            "M file1.py\nM file2.md\nM file3.js\nM file4.py\n?? unstaged.txt"
        )

        # Call get_staged_files with Python file filter
        result = get_staged_files(file_type=".py")

        # Assert mock was called correctly
        mock_run_subprocess.assert_called_once_with(["git", "status", "-s"])

        # Assert only Python files are returned
        self.assertEqual(result, ["file1.py", "file4.py"])

    @patch("os.path.exists")
    @patch("gac.git.run_subprocess")
    def test_get_staged_files_existing_only(self, mock_run_subprocess, mock_exists):
        """Test get_staged_files with existing_only filter returns correct result."""
        # Mock run_subprocess to return staged files
        mock_run_subprocess.return_value = "M file1.py\nM file2.py\nM file3.py"

        # Mock os.path.exists to return True for specific files
        mock_exists.side_effect = lambda f: f != "file2.py"  # file2.py doesn't exist

        # Call get_staged_files with Python file filter and existing_only=True
        result = get_staged_files(file_type=".py", existing_only=True)

        # Assert only existing Python files are returned
        self.assertEqual(result, ["file1.py", "file3.py"])

    @patch("gac.git.run_subprocess")
    def test_git_commit_changes(self, mock_run_subprocess):
        """Test commit_changes calls git commit with the provided message."""
        # Setup mock to avoid actual git command execution
        mock_run_subprocess.return_value = "Commit successful"

        # Call commit_changes
        result = commit_changes("Test commit message")

        # Assert git commit was called with the message
        mock_run_subprocess.assert_called_once_with(["git", "commit", "-m", "Test commit message"])

        # Assert result is True
        self.assertTrue(result)

    def test_commit_changes_empty_message(self):
        """Test commit_changes returns False for empty message."""
        # Call commit_changes with empty message
        result = commit_changes("")

        # Assert result is False
        self.assertFalse(result)

    @patch("gac.git.run_subprocess")
    def test_commit_changes_failure(self, mock_run_subprocess):
        """Test commit_changes returns False when git commit fails."""
        # Setup mock to raise CalledProcessError
        mock_run_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["git", "commit"], "Error output"
        )

        # Call commit_changes
        result = commit_changes("Test commit message")

        # Assert result is False
        self.assertFalse(result)

    @patch("gac.git.run_subprocess")
    def test_stage_files(self, mock_run_subprocess):
        """Test stage_files calls git add with the provided files."""
        # Setup mock
        mock_run_subprocess.return_value = "Files staged"

        # Call stage_files
        result = stage_files(["file1.py", "file2.py"])

        # Assert git add was called with the files
        mock_run_subprocess.assert_called_once_with(["git", "add", "file1.py", "file2.py"])

        # Assert result is True
        self.assertTrue(result)

    def test_stage_files_empty_list(self):
        """Test stage_files returns False for empty file list."""
        # Call stage_files with empty list
        result = stage_files([])

        # Assert result is False
        self.assertFalse(result)

    @patch("gac.git.run_subprocess")
    def test_stage_files_failure(self, mock_run_subprocess):
        """Test stage_files returns False when git add fails."""
        # Setup mock to raise CalledProcessError
        mock_run_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["git", "add"], "Error output"
        )

        # Call stage_files
        result = stage_files(["file1.py", "file2.py"])

        # Assert result is False
        self.assertFalse(result)

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="Project description from file")
    @patch("gac.git.run_subprocess")
    def test_get_project_description(self, mock_run_subprocess, mock_file, mock_exists):
        """Test get_project_description returns repo name and description."""
        # Mock git commands to return expected values
        mock_run_subprocess.side_effect = [
            "/path/to/.git",  # git rev-parse --git-dir
            "https://github.com/user/test-repo.git",  # git config --get remote.origin.url
        ]

        # Mock os.path.exists to return True for description file
        mock_exists.return_value = True

        # Call get_project_description
        result = get_project_description()

        # Assert result contains both repo name and description
        self.assertEqual(
            result, "Repository: test-repo; Description: Project description from file"
        )

    @patch("gac.git.run_subprocess")
    @patch("gac.git.count_tokens")
    def test_is_large_file(self, mock_count_tokens, mock_run_subprocess):
        """Test is_large_file correctly identifies large files."""
        # Set up mock token counting
        mock_count_tokens.side_effect = [
            1001,  # large_file.txt
            999,  # small_file.txt
        ]

        # Test known large file patterns (these don't need token counting)
        self.assertTrue(is_large_file("package-lock.json"))
        self.assertTrue(is_large_file("pnpm-lock.yaml"))
        self.assertTrue(is_large_file("yarn.lock"))

        # Test large token count
        mock_run_subprocess.return_value = "diff content"
        self.assertTrue(is_large_file("large_file.txt"))

        # Test small token count
        mock_run_subprocess.return_value = "diff content"
        self.assertFalse(is_large_file("small_file.txt"))

        # Test error handling
        mock_run_subprocess.side_effect = subprocess.CalledProcessError(1, ["git", "diff"])
        self.assertFalse(is_large_file("error_file.txt"))

    @patch("gac.git.get_staged_files")
    @patch("gac.git.get_file_diff")
    def test_get_staged_diff(self, mock_get_file_diff, mock_get_staged_files):
        """Test get_staged_diff handles large files correctly."""
        # Mock staged files
        mock_get_staged_files.return_value = ["normal.py", "pnpm-lock.yaml", "small.txt"]

        # Use a shorter model name for assertions
        model = "anthropic:claude-3-5-haiku-latest"

        # Mock file diffs
        mock_get_file_diff.side_effect = [
            "normal diff",  # normal.py
            (
                "# Large file pnpm-lock.yaml (truncated):\n"
                "# File type: .yaml\n"
                "# Changes: 2000 tokens\n..."
            ),  # pnpm-lock.yaml (large file)
            "small diff",  # small.txt
        ]

        # Call get_staged_diff
        diff, truncated = get_staged_diff()

        # Check that get_file_diff was called for each file
        self.assertEqual(mock_get_file_diff.call_count, 3)
        mock_get_file_diff.assert_any_call("normal.py", model)
        mock_get_file_diff.assert_any_call("pnpm-lock.yaml", model)
        mock_get_file_diff.assert_any_call("small.txt", model)

        # Check that large file was truncated
        self.assertIn("pnpm-lock.yaml", truncated)
        self.assertIn("Large file pnpm-lock.yaml (truncated):", diff)
        self.assertIn("File type: .yaml", diff)
        self.assertIn("Changes: 2000 tokens", diff)

        # Check that normal files were included fully
        self.assertIn("normal diff", diff)
        self.assertIn("small diff", diff.split("\n"))

        # Test error handling
        mock_get_file_diff.side_effect = ["", "", ""]
        diff, truncated = get_staged_diff()
        self.assertEqual(diff, "")
        self.assertEqual(truncated, [])

    @patch("gac.git.run_subprocess")
    @patch("gac.git.count_tokens")
    def test_get_file_diff(self, mock_count_tokens, mock_run_subprocess):
        """Test get_file_diff handles large files and errors correctly."""
        # Test normal file
        mock_run_subprocess.return_value = "normal diff"
        mock_count_tokens.return_value = 100
        result = get_file_diff("normal.py")
        self.assertEqual(result, "normal diff")

        # Test large file
        mock_run_subprocess.return_value = "large diff content"
        mock_count_tokens.return_value = 2000
        with patch("gac.git.is_large_file", return_value=True):
            result = get_file_diff("large.lock")
        self.assertIn("Large file large.lock (truncated):", result)
        self.assertIn("Changes: 2000 tokens", result)

        # Test empty diff
        mock_run_subprocess.return_value = ""
        result = get_file_diff("empty.py")
        self.assertEqual(result, "")

        # Test error handling
        mock_run_subprocess.side_effect = subprocess.CalledProcessError(1, ["git", "diff"])
        result = get_file_diff("error.py")
        self.assertTrue(result.startswith("# Error processing error.py:"))

    def test_file_status_class(self):
        """Test FileStatus class constants and helper methods."""
        # Test status constants
        self.assertEqual(FileStatus.MODIFIED, "M")
        self.assertEqual(FileStatus.ADDED, "A")
        self.assertEqual(FileStatus.DELETED, "D")
        self.assertEqual(FileStatus.RENAMED, "R")

        # Test is_valid_status method
        self.assertTrue(FileStatus.is_valid_status("M"))
        self.assertTrue(FileStatus.is_valid_status("A"))
        self.assertTrue(FileStatus.is_valid_status("D"))
        self.assertTrue(FileStatus.is_valid_status("R"))
        self.assertFalse(FileStatus.is_valid_status("X"))  # Invalid status
        self.assertFalse(FileStatus.is_valid_status("??"))  # Untracked files


if __name__ == "__main__":
    unittest.main()
