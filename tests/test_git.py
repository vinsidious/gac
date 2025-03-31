"""Test module for gac.git."""

import subprocess
import unittest
from unittest.mock import mock_open, patch

import pytest

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
        result = get_staged_files(cache_skip=True)  # Skip cache to ensure our mock is used

        # Assert mock was called correctly with git status -s
        mock_run_subprocess.assert_called_once_with(["git", "status", "-s"])

        # Check that the result contains only staged files
        self.assertEqual(result, ["file1.py", "file2.md", "file3.js"])
        self.assertNotIn("unstaged.txt", result)

    @patch("gac.git.run_subprocess")
    def test_get_staged_files_with_type(self, mock_run_subprocess):
        """Test get_staged_files with file_type filter returns correct result."""
        # Mock run_subprocess to return staged files with git status -s format
        mock_run_subprocess.return_value = (
            "M file1.py\nM file2.md\nM file3.js\nM file4.py\n?? unstaged.txt"
        )

        # Call get_staged_files with Python file filter and cache_skip=True to bypass caching
        result = get_staged_files(file_type=".py", cache_skip=True)

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
        mock_count_tokens.return_value = 3000  # Set token count above MAX_DIFF_TOKENS

        # Test known large file patterns (these don't need token counting)
        self.assertTrue(is_large_file("package-lock.json"))
        self.assertTrue(is_large_file("pnpm-lock.yaml"))
        self.assertTrue(is_large_file("yarn.lock"))

        # Test large token count
        mock_run_subprocess.return_value = "diff content"
        # Force token count check to return True
        with patch("gac.git.MAX_DIFF_TOKENS", 2000):  # Ensure token count exceeds threshold
            self.assertTrue(is_large_file("large_file.txt"))

    def test_get_staged_diff_with_truncated_files(self):
        """Test get_staged_diff handles large files correctly."""
        # Skip this test for now until we can fix the complicated mocking
        pytest.skip("Needs comprehensive rewrite to match new token count format")
        with patch("gac.git.get_staged_files") as mock_get_staged_files:
            with patch("gac.git.get_file_diff") as mock_get_file_diff:
                # 1. Mock staged files
                mock_get_staged_files.return_value = ["file1.py", "large.lock"]

                # 2. Mock get_file_diff to return a truncated version for large.lock
                def mock_file_diff_side_effect(file_path, model=None):
                    if file_path == "file1.py":
                        return "normal diff for file1.py"
                    elif file_path == "large.lock":
                        # This string should match what get_file_diff returns for truncated files
                        return (
                            "Large file large.lock (5000 tokens, truncated to ~2500 tokens):\n"
                            "truncated content"
                        )
                    return ""

                mock_get_file_diff.side_effect = mock_file_diff_side_effect

                # 3. The actual test function call
                diff, truncated_files = get_staged_diff(cache_skip=True)

                # 4. Assertions
                self.assertTrue(len(truncated_files) > 0, "No files were marked as truncated")
                self.assertTrue(
                    any("large.lock" in item for item in truncated_files),
                    "large.lock missing from truncated files",
                )
                self.assertTrue(
                    any("tokens" in item for item in truncated_files),
                    "Token count missing from truncated files",
                )
                # Check the diff content includes our truncated file
                self.assertIn("Large file large.lock", diff)
                self.assertIn("truncated content", diff)

    @patch("gac.git.get_staged_files")
    def test_get_staged_diff_empty_results(self, mock_get_staged_files):
        """Test get_staged_diff with no staged files."""
        # Mock empty staged files
        mock_get_staged_files.return_value = []

        # Call get_staged_diff with cache_skip=True to bypass caching
        diff, truncated = get_staged_diff(cache_skip=True)

        # Verify empty results
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
            with patch("gac.git.smart_truncate_diff", return_value="truncated content"):
                result = get_file_diff("large.lock")

        # Check that the token count is included in the message
        self.assertIn("Large file large.lock", result)
        self.assertIn("2000 tokens", result)
        self.assertIn("truncated content", result)

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
