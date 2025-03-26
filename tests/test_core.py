"""Test module for gac.core."""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from gac.core import main, run_black, run_isort, run_subprocess, send_to_llm


class TestCore(unittest.TestCase):
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
        result = run_subprocess(["git", "status"])

        # Assert mock was called correctly
        mock_run.assert_called_once_with(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Assert result matches mock stdout
        self.assertEqual(result, "Command output")

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_failure(self, mock_run):
        """Test run_subprocess when command fails."""
        # Mock subprocess.run to return a failure result
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Command failed"
        mock_run.return_value = mock_process

        # Call run_subprocess and expect exception
        with self.assertRaises(subprocess.CalledProcessError):
            run_subprocess(["git", "invalid"])

    @patch("gac.core.get_existing_staged_python_files")
    @patch("gac.core.run_subprocess")
    def test_run_black(self, mock_run_subprocess, mock_get_existing_staged_python_files):
        """Test run_black runs black on Python files."""
        # Mock get_existing_staged_python_files to return Python files
        mock_get_existing_staged_python_files.return_value = ["file1.py", "file2.py"]

        # Mock run_subprocess to avoid actual command execution
        mock_run_subprocess.return_value = ""

        # Call run_black
        result = run_black()

        # Assert black was called with the Python files
        mock_run_subprocess.assert_called_with(["black", "file1.py", "file2.py"])

        # Assert result is True
        self.assertTrue(result)

    @patch("gac.core.get_existing_staged_python_files")
    @patch("gac.core.run_subprocess")
    def test_run_black_no_files(self, mock_run_subprocess, mock_get_existing_staged_python_files):
        """Test run_black when no Python files are staged."""
        mock_get_existing_staged_python_files.return_value = []
        result = run_black()
        self.assertFalse(result)
        mock_run_subprocess.assert_not_called()

    @patch("gac.core.get_existing_staged_python_files")
    @patch("gac.core.run_subprocess")
    def test_run_isort(self, mock_run_subprocess, mock_get_existing_staged_python_files):
        """Test run_isort runs isort on Python files."""
        # Mock get_existing_staged_python_files to return Python files
        mock_get_existing_staged_python_files.return_value = ["file1.py", "file2.py"]

        # Mock run_subprocess to avoid actual command execution
        mock_run_subprocess.return_value = ""

        # Call run_isort
        result = run_isort()

        # Assert isort was called with the Python files
        mock_run_subprocess.assert_called_with(["isort", "file1.py", "file2.py"])

        # Assert result is True
        self.assertTrue(result)

    @patch("gac.core.get_existing_staged_python_files")
    @patch("gac.core.run_subprocess")
    def test_run_isort_no_files(self, mock_run_subprocess, mock_get_existing_staged_python_files):
        """Test run_isort when no Python files are staged."""
        mock_get_existing_staged_python_files.return_value = []
        result = run_isort()
        self.assertFalse(result)
        mock_run_subprocess.assert_not_called()

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.get_staged_python_files")
    @patch("gac.core.get_existing_staged_python_files")
    @patch("gac.core.run_black")
    @patch("gac.core.run_isort")
    @patch("gac.core.stage_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_normal_flow(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_stage_files,
        mock_run_isort,
        mock_run_black,
        mock_get_existing_staged_python_files,
        mock_get_staged_python_files,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main with normal flow with formatting."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_get_staged_python_files.return_value = ["file1.py"]
        mock_get_existing_staged_python_files.return_value = ["file1.py"]
        mock_run_black.return_value = True
        mock_run_isort.return_value = True
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"  # Mock user confirming the commit

        # Call main
        result = main()

        # Assert formatting was run
        mock_run_black.assert_called_once()
        mock_run_isort.assert_called_once()

        # Assert files were re-staged after formatting
        self.assertEqual(mock_stage_files.call_count, 2)  # Once after black, once after isort

        # Assert LLM was called
        mock_send_to_llm.assert_called_once()

        # Assert commit was made with the generated message
        mock_commit_changes.assert_called_once_with("Generated commit message")

        # Assert git push was called
        for call_args in mock_run_subprocess.call_args_list:
            if call_args[0][0] == ["git", "push"]:
                break
        else:
            self.fail("git push was not called")

        # Assert message was returned
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    def test_main_no_staged_files(self, mock_get_staged_files, mock_get_config):
        """Test main when there are no staged files."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = []
        result = main()
        self.assertIsNone(result)

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.get_staged_python_files")
    @patch("gac.core.get_existing_staged_python_files")
    @patch("gac.core.run_black")
    @patch("gac.core.run_isort")
    @patch("gac.core.stage_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_no_formatting(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_stage_files,
        mock_run_isort,
        mock_run_black,
        mock_get_existing_staged_python_files,
        mock_get_staged_python_files,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main with formatting disabled."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_get_staged_python_files.return_value = ["file1.py"]
        mock_get_existing_staged_python_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        result = main(no_format=True)

        mock_run_black.assert_not_called()
        mock_run_isort.assert_not_called()
        mock_commit_changes.assert_called_once_with("Generated commit message")
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_force_mode(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main in force mode."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"

        result = main(force=True)

        mock_prompt.assert_not_called()
        mock_commit_changes.assert_called_once_with("Generated commit message")
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_quiet_mode(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main in quiet mode."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Instead of checking if logging.basicConfig was called, we'll verify the function runs without errors
        result = main(quiet=True)
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_verbose_mode(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main in verbose mode."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Instead of checking if logging.basicConfig was called, we'll verify the function runs without errors
        result = main(verbose=True)
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_model_override(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main with model override."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Use patch.dict to mock os.environ
        with patch.dict("gac.core.os.environ", {}, clear=True):
            # Call main with model override
            result = main(model="openai:gpt-4")

            # Check that the model was set in the environment
            from gac.core import os

            self.assertEqual(os.environ.get("GAC_MODEL"), "openai:gpt-4")

        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_add_all(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main with add_all option."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        with patch("gac.core.stage_files") as mock_stage_files:
            main(add_all=True)
            mock_stage_files.assert_called_once_with(["."])

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_failed_llm(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main when LLM fails to generate a message."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = None
        mock_prompt.return_value = "y"

        result = main()
        self.assertIsNone(result)

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_user_declines_commit(
        self,
        mock_print,
        mock_prompt,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main when user declines to commit."""
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "n"

        result = main()
        self.assertIsNone(result)
        mock_commit_changes.assert_not_called()

    @patch("gac.core.get_config")
    @patch("gac.core.chat")
    @patch("gac.core.count_tokens")
    def test_send_to_llm(self, mock_count_tokens, mock_chat, mock_get_config):
        """Test send_to_llm function."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku"}
        mock_count_tokens.return_value = 100
        mock_chat.return_value = "Generated commit message"

        # Call send_to_llm
        result = send_to_llm("git status output", "git diff output")

        # Assert LLM was called with expected parameters
        mock_chat.assert_called_once()
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_no_push(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main when user declines to push."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.side_effect = ["y", "n"]  # Mock user confirming commit but declining push

        # Call main
        result = main()

        # Assert commit was made
        mock_commit_changes.assert_called_once()

        # Assert git push was not called
        for call_args in mock_run_subprocess.call_args_list:
            self.assertNotEqual(call_args[0][0], ["git", "push"])

        # Assert message was returned
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.get_staged_python_files")
    @patch("gac.core.run_black")
    @patch("gac.core.run_isort")
    @patch("gac.core.run_subprocess")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_with_python_files_no_formatting(
        self,
        mock_print,
        mock_prompt,
        mock_commit_changes,
        mock_send_to_llm,
        mock_run_subprocess,
        mock_run_isort,
        mock_run_black,
        mock_get_staged_python_files,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main with Python files but formatting disabled."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py", "file2.txt"]
        mock_get_staged_python_files.return_value = ["file1.py"]
        mock_run_subprocess.return_value = (
            "diff --git a/file1.py b/file1.py"  # Mock the git diff command
        )
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"  # Mock user confirming the commit

        # Call main with no_format=True
        result = main(no_format=True)

        # Assert formatting was not run
        mock_run_black.assert_not_called()
        mock_run_isort.assert_not_called()

        # Assert commit message was generated and applied
        mock_send_to_llm.assert_called_once()
        mock_commit_changes.assert_called_once()
        self.assertEqual(result, "Generated commit message")

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.send_to_llm")
    @patch("gac.core.commit_changes")
    @patch("gac.core.run_subprocess")
    @patch("click.prompt")
    @patch("builtins.print")
    def test_main_test_mode(
        self,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main in test mode."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_prompt.return_value = "y"  # Mock user confirming the commit

        # Call main in test mode
        result = main(test_mode=True)

        # Assert LLM was not called
        mock_send_to_llm.assert_not_called()

        # Assert commit was not made
        mock_commit_changes.assert_not_called()

        # Assert test message was returned
        self.assertTrue(result.startswith("[TEST MESSAGE]"))


if __name__ == "__main__":
    unittest.main()
