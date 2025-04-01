"""Test module for gac.git_operations."""

import subprocess
import unittest
from unittest.mock import patch

from gac.git_operations import GitOperationsManager


class TestGitOperationsManager(unittest.TestCase):
    """Tests for GitOperationsManager class."""

    def setUp(self):
        """Set up test environment."""
        self.git_manager = GitOperationsManager(quiet=True)

    def test_ensure_git_directory_success(self):
        """Test ensure_git_directory returns the git root when successful."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "/path/to/git/repo\n"
            with patch("os.getcwd", return_value="/path/to/git/repo"):
                with patch("os.chdir") as mock_chdir:
                    result = self.git_manager.ensure_git_directory()

                    # Verify the result is the git root directory
                    self.assertEqual(result, "/path/to/git/repo")

                    # Verify we didn't need to change directory
                    mock_chdir.assert_not_called()

    def test_ensure_git_directory_changes_dir(self):
        """Test ensure_git_directory changes to git root when in subdirectory."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "/path/to/git/repo\n"
            with patch("os.getcwd", return_value="/path/to/git/repo/subdirectory"):
                with patch("os.chdir") as mock_chdir:
                    result = self.git_manager.ensure_git_directory()

                    # Verify the result is the git root directory
                    self.assertEqual(result, "/path/to/git/repo")

                    # Verify we changed to the git root directory
                    mock_chdir.assert_called_once_with("/path/to/git/repo")

    def test_ensure_git_directory_not_a_git_repo(self):
        """Test ensure_git_directory returns None when not in a git repository."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                128, ["git", "rev-parse"], stderr="Not a git repository"
            )
            result = self.git_manager.ensure_git_directory()

            # Verify the result is None
            self.assertIsNone(result)

    def test_stage_all_files_success(self):
        """Test stage_all_files successfully stages all files."""
        with patch.object(
            self.git_manager, "get_status", return_value="Changes not staged for commit"
        ):
            with patch.object(self.git_manager, "stage_files", return_value=True):
                result = self.git_manager.stage_all_files()

                # Verify the result is True
                self.assertTrue(result)

                # Verify stage_files was called with '.'
                self.git_manager.stage_files.assert_called_once_with(["."])

    def test_stage_all_files_empty_repo(self):
        """Test stage_all_files handles empty repository correctly."""
        with patch.object(self.git_manager, "get_status", return_value="No commits yet"):
            with patch("subprocess.run") as mock_run:
                # First run is for adding files
                # Second run is for initial commit
                # Third run might be for staging files again if needed
                mock_run.return_value.stdout = "Success"

                result = self.git_manager.stage_all_files()

                # Verify the result is True
                self.assertTrue(result)

                # Verify subprocess.run was called at least twice (add + commit)
                self.assertGreaterEqual(mock_run.call_count, 2)

    def test_get_staged_files_success(self):
        """Test get_staged_files returns a list of staged files."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "file1.py\nfile2.py\n"

            result = self.git_manager.get_staged_files()

            # Verify the result is a list of staged files
            self.assertEqual(result, ["file1.py", "file2.py"])

    def test_get_staged_files_error(self):
        """Test get_staged_files returns empty list on error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "diff"], stderr="Git error"
            )

            result = self.git_manager.get_staged_files()

            # Verify the result is an empty list
            self.assertEqual(result, [])

    def test_get_staged_diff_success(self):
        """Test get_staged_diff returns the diff of staged changes."""
        expected_diff = "diff --git a/file1.py b/file1.py\n+New line"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = expected_diff

            result = self.git_manager.get_staged_diff()

            # Verify the result is the expected diff
            self.assertEqual(result, expected_diff)

    def test_get_staged_diff_error(self):
        """Test get_staged_diff returns empty string on error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "diff"], stderr="Git error"
            )

            result = self.git_manager.get_staged_diff()

            # Verify the result is an empty string
            self.assertEqual(result, "")

    def test_stage_files_success(self):
        """Test stage_files successfully stages specified files."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "Success"

            result = self.git_manager.stage_files(["file1.py", "file2.py"])

            # Verify the result is True
            self.assertTrue(result)

            # Verify subprocess.run was called twice (once for each file)
            self.assertEqual(mock_run.call_count, 2)

    def test_stage_files_error(self):
        """Test stage_files returns False on error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "add"], stderr="Git error"
            )

            result = self.git_manager.stage_files(["file1.py"])

            # Verify the result is False
            self.assertFalse(result)

    def test_commit_changes_success(self):
        """Test commit_changes successfully commits staged changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "Success"

            result = self.git_manager.commit_changes("Test commit message")

            # Verify the result is True
            self.assertTrue(result)

            # Verify subprocess.run was called with the correct commit message
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "git")
            self.assertEqual(args[1], "commit")
            self.assertEqual(args[3], "Test commit message")

    def test_commit_changes_error(self):
        """Test commit_changes returns False on error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "commit"], stderr="Git error"
            )

            result = self.git_manager.commit_changes("Test commit message")

            # Verify the result is False
            self.assertFalse(result)

    def test_push_changes_success(self):
        """Test push_changes successfully pushes commits to remote."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "Success"

            result = self.git_manager.push_changes()

            # Verify the result is True
            self.assertTrue(result)

            # Verify subprocess.run was called with git push
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "git")
            self.assertEqual(args[1], "push")

    def test_push_changes_error(self):
        """Test push_changes returns False on error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "push"], stderr="Git error"
            )

            result = self.git_manager.push_changes()

            # Verify the result is False
            self.assertFalse(result)
