"""Test module for gac.git."""

import subprocess
import unittest
from unittest.mock import mock_open, patch

from gac.git import (
    commit_changes,
    get_existing_staged_python_files,
    get_project_description,
    get_staged_diff,
    get_staged_files,
    get_staged_python_files,
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

    @patch("gac.git.get_staged_files")
    def test_get_staged_python_files(self, mock_get_staged_files):
        """Test get_staged_python_files returns only Python files."""
        # Mock get_staged_files to return mixed file types
        mock_get_staged_files.return_value = ["file1.py", "file2.md", "file3.js", "file4.py"]

        # Call get_staged_python_files
        result = get_staged_python_files()

        # Assert only Python files are returned
        self.assertEqual(result, ["file1.py", "file4.py"])

    @patch("os.path.exists")
    @patch("gac.git.get_staged_python_files")
    def test_get_existing_staged_python_files(self, mock_get_staged_python_files, mock_exists):
        """Test get_existing_staged_python_files returns only existing Python files."""
        # Mock get_staged_python_files to return Python files
        mock_get_staged_python_files.return_value = ["file1.py", "file2.py", "file3.py"]

        # Mock os.path.exists to return True for specific files
        mock_exists.side_effect = lambda f: f != "file2.py"  # file2.py doesn't exist

        # Call get_existing_staged_python_files
        result = get_existing_staged_python_files()

        # Assert only existing Python files are returned
        self.assertEqual(result, ["file1.py", "file3.py"])

    @patch("gac.git.run_subprocess")
    def test_git_commit_changes(self, mock_run_subprocess):
        """Test commit_changes calls git commit with the provided message."""
        # Setup mock to avoid actual git command execution
        mock_run_subprocess.return_value = "Commit successful"

        # Call commit_changes
        commit_changes("Test commit message")

        # Assert git commit was called with the message
        mock_run_subprocess.assert_called_once_with(["git", "commit", "-m", "Test commit message"])

    def test_commit_changes_empty_message(self):
        """Test commit_changes raises ValueError for empty message."""
        # Call commit_changes with empty message and expect ValueError
        with self.assertRaises(ValueError):
            commit_changes("")

    @patch("gac.git.run_subprocess")
    def test_commit_changes_failure(self, mock_run_subprocess):
        """Test commit_changes raises CalledProcessError when git commit fails."""
        # Setup mock to raise CalledProcessError
        mock_run_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["git", "commit"], "Error output"
        )

        # Call commit_changes and expect CalledProcessError
        with self.assertRaises(subprocess.CalledProcessError):
            commit_changes("Test commit message")

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
        """Test stage_files raises ValueError for empty file list."""
        # Call stage_files with empty list and expect ValueError
        with self.assertRaises(ValueError):
            stage_files([])

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
    @patch("aisuite.Client")
    def test_is_large_file(self, mock_client, mock_run_subprocess):
        """Test is_large_file correctly identifies large files."""
        # Set up mock client for token counting
        mock_client_instance = mock_client.return_value
        mock_client_instance.count_tokens.side_effect = [
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
    @patch("gac.git.run_subprocess")
    @patch("aisuite.Client")
    def test_get_staged_diff(self, mock_client, mock_run_subprocess, mock_get_staged_files):
        """Test get_staged_diff handles large files correctly."""
        # Set up mock client for token counting
        mock_client_instance = mock_client.return_value
        mock_client_instance.count_tokens.side_effect = [
            100,  # normal.py
            2000,  # pnpm-lock.yaml
            50,  # small.txt
        ]  # Only pnpm-lock.yaml is large

        # Mock staged files
        mock_get_staged_files.return_value = ["normal.py", "pnpm-lock.yaml", "small.txt"]

        # Mock diffs for each file
        # For each file, we need to mock:
        # 1. The call in is_large_file to check if it's large
        # 2. The call in get_staged_diff to get the actual diff (except for large files)
        mock_run_subprocess.side_effect = [
            # normal.py
            "normal diff",  # is_large_file check
            "normal diff",  # get_staged_diff
            # pnpm-lock.yaml (large file - only needs one check)
            "large diff content",  # is_large_file check
            # small.txt
            "small diff",  # is_large_file check
            "small diff",  # get_staged_diff
        ]

        diff, truncated = get_staged_diff()

        # Debug assertions to understand mock call sequence
        print("\nActual calls:")
        for i, call in enumerate(mock_run_subprocess.call_args_list):
            print(f"Call {i}: {call[0][0][-1]}")

        self.assertEqual(
            len(mock_run_subprocess.call_args_list), 5
        )  # 2 calls for normal files, 1 for large files
        self.assertEqual(mock_run_subprocess.call_args_list[0][0][0][-1], "normal.py")
        self.assertEqual(mock_run_subprocess.call_args_list[2][0][0][-1], "pnpm-lock.yaml")
        self.assertEqual(mock_run_subprocess.call_args_list[3][0][0][-1], "small.txt")

        # Check that large file was truncated
        self.assertIn("pnpm-lock.yaml", truncated)
        self.assertIn("Large file pnpm-lock.yaml (truncated):", diff)
        self.assertIn("File type: .yaml", diff)
        self.assertIn("Changes: 2000 tokens", diff)

        # Check that normal files were included fully
        self.assertIn("normal diff", diff)
        self.assertIn(
            "small diff", diff.split("\n")
        )  # Check if "small diff" exists as a line in the diff

        # Test error handling
        mock_run_subprocess.side_effect = subprocess.CalledProcessError(1, ["git", "diff"])
        diff, truncated = get_staged_diff()
        self.assertEqual(diff, "")
        self.assertEqual(truncated, [])


if __name__ == "__main__":
    unittest.main()
