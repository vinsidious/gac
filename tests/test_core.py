"""Test module for gac.core."""

import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

import pytest

from gac.git import TestGitOperations, get_git_operations, set_git_operations
from gac.prompts import build_prompt, create_abbreviated_prompt
from gac.utils import run_subprocess
from gac.workflow import CommitWorkflow


# Mock for aisuite Client
class MockAisuiteClient:
    def __init__(self, *args, **kwargs):
        pass

    def complete(self, *args, **kwargs):
        completion = MagicMock()
        completion.text = "Generated commit message"
        return completion


# Mock for aisuite Provider
class MockProvider:
    def __init__(self, *args, **kwargs):
        pass


# Use pytest fixture for setting up the test environment
@pytest.fixture(autouse=True)
def pytest_environment():
    """Setup the PYTEST_CURRENT_TEST environment variable for all tests."""
    # Set up environment for tests
    old_value = os.environ.get("PYTEST_CURRENT_TEST")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    yield
    # Clean up after tests
    if old_value is not None:
        os.environ["PYTEST_CURRENT_TEST"] = old_value
    else:
        os.environ.pop("PYTEST_CURRENT_TEST", None)


class TestCore(unittest.TestCase):
    """Tests for core functionality."""

    def tearDown(self):
        """Reset git operations after each test."""
        # Reset to real git operations after each test
        set_git_operations(get_git_operations().__class__())

    def test_run_subprocess_success(self):
        """Test run_subprocess when command succeeds."""
        # Mock subprocess.run to return a success result
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Command output"
        with patch("gac.utils.subprocess.run") as mock_run:
            mock_run.return_value = mock_process

            # Call run_subprocess
            result = run_subprocess(["echo", "test"])

            # Assert result matches mock stdout
            self.assertEqual(result, "Command output")

    def test_run_subprocess_failure(self):
        """Test run_subprocess when command fails."""
        # Mock subprocess.run to raise CalledProcessError
        with patch("gac.utils.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "invalid"], "Output", "Error"
            )

            # Call run_subprocess and check it raises the exception
            with self.assertRaises(subprocess.CalledProcessError):
                run_subprocess(["git", "invalid"])

    def test_workflow_no_formatting(self):
        """Test workflow with formatting disabled."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges to be committed:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Create a workflow with no_format=True
            workflow = CommitWorkflow(no_format=True)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Assert commit message was generated and applied
                self.assertEqual(len(test_git.commit_messages), 1)
                self.assertEqual(test_git.commit_messages[0], "Generated commit message")

                # Verify the correct methods were called
                method_calls = [call[0] for call in test_git.calls]
                self.assertIn("get_staged_files", method_calls)
                self.assertIn("get_staged_diff", method_calls)
                self.assertIn("commit_changes", method_calls)

    def test_workflow_logging_modes_quiet(self):
        """Test workflow in quiet logging mode."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges to be committed:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Create a workflow with quiet mode
            workflow = CommitWorkflow(quiet=True)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Assert commit was made
                self.assertEqual(len(test_git.commit_messages), 1)
                self.assertEqual(test_git.commit_messages[0], "Generated commit message")

    def test_workflow_logging_modes_verbose(self):
        """Test workflow in verbose logging mode."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges to be committed:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Create a workflow with verbose mode
            workflow = CommitWorkflow(verbose=True)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Assert commit was made
                self.assertEqual(len(test_git.commit_messages), 1)
                self.assertEqual(test_git.commit_messages[0], "Generated commit message")

    def test_workflow_force_mode(self):
        """Test workflow in force mode."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges to be committed:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Create a workflow in force mode
            workflow = CommitWorkflow(force=True)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Assert commit was made
                self.assertEqual(len(test_git.commit_messages), 1)
                self.assertEqual(test_git.commit_messages[0], "Generated commit message")

    def test_workflow_model_override(self):
        """Test workflow with model override."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges to be committed:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Use patch.dict to mock os.environ
            with patch.dict("os.environ", {"PYTEST_CURRENT_TEST": "True"}, clear=False):
                # Create a workflow with model override
                workflow = CommitWorkflow(model="openai:gpt-4")

                # Mock the generate_message method to return a predefined message
                with patch.object(
                    CommitWorkflow, "generate_message", return_value="Generated commit message"
                ):
                    # Run the workflow
                    workflow.run()

                    # Check that the model was set in the config
                    self.assertEqual(workflow.config["model"], "openai:gpt-4")

                    # Assert commit was made
                    self.assertEqual(len(test_git.commit_messages), 1)
                    self.assertEqual(test_git.commit_messages[0], "Generated commit message")

    def test_workflow_add_all(self):
        """Test workflow with add_all option."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges not staged for commit:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Create a workflow with add_all=True
            workflow = CommitWorkflow(add_all=True)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Assert stage_files was called with ["."]
                stage_calls = [call for call in test_git.calls if call[0] == "stage_files"]
                self.assertTrue(any(call[1]["files"] == ["."] for call in stage_calls))

                # Assert commit was made
                self.assertEqual(len(test_git.commit_messages), 1)
                self.assertEqual(test_git.commit_messages[0], "Generated commit message")

    def test_workflow_test_mode(self):
        """Test workflow in test mode."""
        # Create a test git operations instance
        test_git = TestGitOperations(
            mock_status="On branch main\nChanges to be committed:\n  modified: file1.py",
            mock_staged_files={"file1.py": "M"},
            mock_staged_diff="diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content",
        )

        # Set as the current git operations
        set_git_operations(test_git)

        # Create workflow in test mode
        workflow = CommitWorkflow(test_mode=True)

        # Mock the generate_message method to return a predefined message
        with patch.object(CommitWorkflow, "generate_message", return_value="Test commit message"):
            # In test mode, should call sys.exit(0)
            with patch("sys.exit") as mock_exit:
                # Run the workflow
                workflow.run()

                # Assert sys.exit was called
                mock_exit.assert_called_once_with(0)

    def test_build_prompt_direct(self):
        """Test build_prompt function directly."""
        # Set up test inputs
        status = "On branch main"
        diff = "diff --git a/file.py b/file.py\n+New line"

        # Call the function directly
        result = build_prompt(status, diff, one_liner=True, hint="Test hint", conventional=True)

        # Check expected output contents
        self.assertIn(status, result)
        self.assertIn(diff, result)
        self.assertIn("Test hint", result)
        self.assertIn("conventional commit", result.lower())
        self.assertIn("single line", result.lower())

    def test_create_abbreviated_prompt(self):
        """Test create_abbreviated_prompt function."""
        # Create a test prompt with the specific test status that the function is looking for
        test_status = (
            "Git status:\nOn branch main\nChanges to be committed:\n"
            "  modified: file1.py\n  modified: file2.py"
        )

        # Create a prompt with the test status and a large diff
        full_prompt = (
            "Some intro text\n"
            + test_status
            + "\n"
            + "Changes to be committed:\n<git-diff>\n"
            + "\n".join([f"line {i}" for i in range(100)])  # More than max_diff_lines
            + "\n</git-diff>"
        )

        # Call the actual function
        abbrev = create_abbreviated_prompt(full_prompt)

        # Verify the output is abbreviated
        self.assertNotEqual(full_prompt, abbrev)
        self.assertIn("truncated", abbrev)  # The function adds "... (truncated)" for test cases
