"""Test module for gac modules."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from gac.prompts import build_prompt, create_abbreviated_prompt
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


class TestCore:
    """Tests for core functions."""

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_success(self, mock_run):
        """Test run_subprocess when command succeeds."""
        # Mock subprocess.run to return a success result
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Command output"
        mock_run.return_value = mock_process

        # Call run_subprocess
        from gac.utils import run_subprocess

        result = run_subprocess(["git", "status"])

        # Assert mock was called with the expected arguments
        mock_run.assert_called_once_with(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60,
        )

        # Assert result matches mock stdout
        assert result == "Command output"

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_failure(self, mock_run):
        """Test run_subprocess when command fails."""
        # Mock subprocess.run to raise CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "invalid"], "Output", "Error"
        )

        # Call run_subprocess and expect exception
        from gac.utils import run_subprocess

        with pytest.raises(subprocess.CalledProcessError):
            run_subprocess(["git", "invalid"])

    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.commit_changes")
    @patch("sys.exit")
    def test_workflow_no_formatting(
        self, mock_exit, mock_commit_changes, mock_get_staged_diff, mock_get_status
    ):
        """Test workflow with formatting disabled."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        mock_commit_changes.return_value = True

        # Create a workflow with no_format=True and explicitly set test mode to False
        workflow = CommitWorkflow(no_format=True, test_mode=False)

        # Mock the sys.exit function to prevent exit
        mock_exit.side_effect = lambda x: None

        # Mock the generate_message method to return a predefined message
        with patch.object(
            CommitWorkflow, "generate_message", return_value="Generated commit message"
        ):
            # Run the workflow
            workflow.run()

            # Assert commit message was generated and applied
            mock_commit_changes.assert_called_once_with("Generated commit message")

    @pytest.mark.parametrize(
        "mode",
        ["quiet", "verbose"],
    )
    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.commit_changes")
    @patch("sys.exit")
    def test_workflow_logging_modes(
        self, mock_exit, mock_commit_changes, mock_get_staged_diff, mock_get_status, mode
    ):
        """Test workflow in different logging modes."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        mock_commit_changes.return_value = True

        # Mock the sys.exit function to prevent exit
        mock_exit.side_effect = lambda x: None

        # Create a workflow with the specified mode and test_mode set to False
        kwargs = {mode: True, "test_mode": False}
        workflow = CommitWorkflow(**kwargs)

        # Mock the generate_message method to return a predefined message
        with patch.object(
            CommitWorkflow, "generate_message", return_value="Generated commit message"
        ):
            # Run the workflow
            workflow.run()

            # Assert commit was made
            mock_commit_changes.assert_called_once_with("Generated commit message")

    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.commit_changes")
    @patch("sys.exit")
    def test_workflow_force_mode(
        self, mock_exit, mock_commit_changes, mock_get_staged_diff, mock_get_status
    ):
        """Test workflow in force mode."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        mock_commit_changes.return_value = True

        # Mock the sys.exit function to prevent exit
        mock_exit.side_effect = lambda x: None

        # Create a workflow in force mode with test_mode set to False
        workflow = CommitWorkflow(force=True, test_mode=False)

        # Mock the generate_message method to return a predefined message
        with patch.object(
            CommitWorkflow, "generate_message", return_value="Generated commit message"
        ):
            # Run the workflow
            workflow.run()

            # Assert commit was made
            mock_commit_changes.assert_called_once_with("Generated commit message")

    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.commit_changes")
    @patch("sys.exit")
    def test_workflow_model_override(
        self, mock_exit, mock_commit_changes, mock_get_staged_diff, mock_get_status
    ):
        """Test workflow with model override."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        mock_commit_changes.return_value = True

        # Mock the sys.exit function to prevent exit
        mock_exit.side_effect = lambda x: None

        # Use patch.dict to mock os.environ
        with patch.dict("os.environ", {"PYTEST_CURRENT_TEST": "True"}, clear=False):
            # Create a workflow with model override and test_mode set to False
            workflow = CommitWorkflow(model="openai:gpt-4", test_mode=False)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Check that the model was set in the config
                assert workflow.config["model"] == "openai:gpt-4"

                # Assert commit was made
                mock_commit_changes.assert_called_once_with("Generated commit message")

    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.commit_changes")
    @patch("gac.git.get_staged_files")
    @patch("gac.git.stage_files")
    @patch("sys.exit")
    def test_workflow_add_all(
        self,
        mock_exit,
        mock_stage_files,
        mock_get_staged_files,
        mock_commit_changes,
        mock_get_staged_diff,
        mock_get_status,
    ):
        """Test workflow with add_all option."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        mock_get_staged_files.return_value = {"file1.py": "M"}
        mock_commit_changes.return_value = True
        mock_stage_files.return_value = True

        # Mock the sys.exit function to prevent exit
        mock_exit.side_effect = lambda x: None

        # Ensure the mocks are not affected by the GAC_TEST_MODE environment variable
        with patch.dict("os.environ", {"GAC_TEST_MODE": "0"}, clear=False):
            # Create a workflow with add_all=True and test_mode set to False
            workflow = CommitWorkflow(add_all=True, test_mode=False)

            # Mock the generate_message method to return a predefined message
            with patch.object(
                CommitWorkflow, "generate_message", return_value="Generated commit message"
            ):
                # Run the workflow
                workflow.run()

                # Assert stage_files was called
                mock_stage_files.assert_called_once_with(["."])

                # Assert commit was made
                mock_commit_changes.assert_called_once_with("Generated commit message")

    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.commit_changes")
    def test_send_to_llm(self, mock_commit_changes, mock_get_staged_diff, mock_get_status):
        """Test _send_to_llm method in CommitWorkflow."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )

        # Create a CommitWorkflow instance
        workflow = CommitWorkflow()

        # The environment variable is already set in setup_method
        # Call the method directly
        result = workflow._send_to_llm("Status text", "Diff text", one_liner=False)

        # Assert the result is correct
        assert result == "Generated commit message"

    @patch("gac.git.get_status")
    @patch("gac.git.get_staged_diff")
    @patch("gac.git.get_staged_files")
    @patch("sys.exit")
    def test_workflow_test_mode(
        self, mock_exit, mock_get_staged_files, mock_get_staged_diff, mock_get_status
    ):
        """Test workflow in test mode."""
        # Set up mocks
        mock_get_staged_diff.return_value = (
            "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        )
        mock_get_status.return_value = (
            "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        mock_get_staged_files.return_value = {"file1.py": "M"}

        # Create workflow in test mode
        workflow = CommitWorkflow(test_mode=True)

        # Mock the generate_message method to return a predefined message
        with patch.object(CommitWorkflow, "generate_message", return_value="Test commit message"):
            # Run the workflow
            workflow.run()

            # Assert sys.exit was called
            mock_exit.assert_called_once_with(0)

    def test_build_prompt_with_hint(self):
        """Test build_prompt function with hint."""
        status = "On branch main\nChanges to be committed:\n  modified: file1.py"
        diff = "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"
        hint = "JIRA-123"

        # Call build_prompt with hint
        prompt = build_prompt(status, diff, False, hint, False)

        # Assert hint is included in the prompt
        assert hint in prompt
        assert "Git status:" in prompt

    def test_build_prompt_conventional_format(self):
        """Test build_prompt function with conventional flag."""
        status = "On branch main\nChanges to be committed:\n  modified: file1.py"
        diff = "diff --git a/file1.py b/file1.py\n@@ -1,1 +1,2 @@\n+New content"

        # Call build_prompt with conventional=True
        prompt = build_prompt(status, diff, False, "", True)

        # Assert conventional commit format is requested in the prompt
        assert (
            "IMPORTANT: EVERY commit message MUST start with a conventional commit prefix" in prompt
        )

    def test_create_abbreviated_prompt(self):
        """Test create_abbreviated_prompt function."""
        full_prompt = """Git status:
On branch main
Changes to be committed:
  modified: file1.py
  modified: file2.py
  modified: file3.py
  modified: file4.py
  modified: file5.py
  modified: file6.py

Git diff:
diff --git a/file1.py b/file1.py
@@ -1,5 +1,6 @@
 Line 1
 Line 2
+New Line 3
 Line 4
 Line 5

diff --git a/file2.py b/file2.py
@@ -10,7 +10,8 @@
 Line 10
 Line 11
-Line 12
+New Line 12
 Line 13
 Line 14
"""

        # Call create_abbreviated_prompt
        abbreviated = create_abbreviated_prompt(full_prompt)

        # Assert the result is shorter than the original
        assert len(abbreviated) < len(full_prompt)
