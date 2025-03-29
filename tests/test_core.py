"""Test module for gac.core."""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from gac.core import build_prompt, main, run_subprocess, send_to_llm


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

    @patch("gac.core.get_config")
    @patch("gac.core.get_staged_files")
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
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main with formatting disabled."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py", "file2.txt"]
        mock_run_subprocess.return_value = "diff --git a/file1.py b/file1.py"
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Call main with no_format=True
        result = main(no_format=True)

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
    @patch("gac.core.logging")
    def test_main_quiet_mode(
        self,
        mock_logging,
        mock_print,
        mock_prompt,
        mock_run_subprocess,
        mock_commit_changes,
        mock_send_to_llm,
        mock_get_staged_files,
        mock_get_config,
    ):
        """Test main in quiet mode."""
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Call main in quiet mode
        result = main(quiet=True)

        # Assert print was not called
        mock_print.assert_not_called()

        # Assert logging was set to ERROR level
        mock_logging.getLogger.return_value.setLevel.assert_called_once_with(mock_logging.ERROR)

        # Assert commit was made
        mock_commit_changes.assert_called_once()
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
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Call main in verbose mode
        result = main(verbose=True)

        # Assert print was called
        mock_print.assert_called()

        # Assert commit was made
        mock_commit_changes.assert_called_once()
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

        # We need to mock the entire flow to avoid multiple stage_files calls
        with patch("gac.core.stage_files") as mock_stage_files:
            with patch("gac.core.get_staged_python_files") as mock_get_staged_python_files:
                with patch(
                    "gac.core.get_existing_staged_python_files"
                ) as mock_get_existing_staged_python_files:
                    mock_get_staged_python_files.return_value = []
                    mock_get_existing_staged_python_files.return_value = []

                    main(add_all=True)

                    # Verify stage_files was called with ["."] for add_all
                    mock_stage_files.assert_any_call(["."])

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
        # Setup mocks
        mock_get_config.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        mock_get_staged_files.return_value = ["file1.py"]
        mock_send_to_llm.return_value = "Generated commit message"
        mock_prompt.return_value = "y"

        # Mock logger to avoid actual logging calls
        with patch("gac.core.logger") as mock_logger:
            # Call main in quiet mode
            result = main(quiet=True)

            # Assert logger level was set to ERROR
            mock_logger.setLevel.assert_called_once()

            # Assert commit was made
            mock_commit_changes.assert_called_once()
            self.assertEqual(result, "Generated commit message")

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

    @patch("gac.core.run_subprocess")
    @patch("gac.core.get_staged_files")
    @patch("builtins.print")
    def test_main_test_mode(self, mock_print, mock_get_staged_files, mock_run_subprocess):
        """Test main function in test mode."""
        # Mock staged files
        mock_get_staged_files.return_value = ["file1.py", "file2.py"]

        # Call main in test mode with testing=True to avoid interactive prompts
        result = main(test_mode=True, testing=True)

        # Assert the result is a test commit message
        self.assertIsNotNone(result)
        self.assertIn("[TEST MESSAGE]", result)

        # Verify prints were called for the test message
        mock_print.assert_any_call("\n=== Test Commit Message ===")
        mock_print.assert_any_call(result)

        # Verify no subprocess calls for commit
        mock_run_subprocess.assert_not_called()

    @patch("gac.core.run_subprocess")
    @patch("gac.core.get_staged_files")
    @patch("gac.core.build_prompt")
    @patch("gac.core.count_tokens")
    @patch("builtins.print")
    def test_main_test_mode_with_real_diff(
        self,
        mock_print,
        mock_count_tokens,
        mock_build_prompt,
        mock_get_staged_files,
        mock_run_subprocess,
    ):
        """Test main function in test mode with real diff option."""
        # Mock staged files
        mock_get_staged_files.return_value = ["file1.py", "file2.py"]

        # Mock subprocess calls for git status and diff
        mock_run_subprocess.side_effect = [
            "M file1.py\nA file2.py",  # git status
            "diff --git a/file1.py b/file1.py\n+test content",  # git diff
        ]

        # Mock build_prompt
        mock_build_prompt.return_value = "Test prompt content"

        # Mock count_tokens
        mock_count_tokens.return_value = 50

        # Call main with test_with_real_diff option and testing=True to avoid interactive prompts
        result = main(test_mode=True, test_with_real_diff=True, testing=True)

        # Assert the result is a test commit message
        self.assertIsNotNone(result)

        # Verify subprocess calls for status and diff
        self.assertEqual(mock_run_subprocess.call_count, 2)
        mock_run_subprocess.assert_any_call(["git", "status"])
        mock_run_subprocess.assert_any_call(["git", "--no-pager", "diff", "--staged"])

        # Verify build_prompt was called
        mock_build_prompt.assert_called_once()

        # Verify count_tokens was called
        mock_count_tokens.assert_called_once()

    @patch("gac.core.run_subprocess")
    @patch("gac.core.get_staged_files")
    @patch("builtins.print")
    def test_main_empty_stage_test_mode(
        self, mock_print, mock_get_staged_files, mock_run_subprocess
    ):
        """Test main function with empty staging area in test mode."""
        # Mock empty staged files
        mock_get_staged_files.return_value = []

        # Call main in test mode with testing=True to avoid interactive prompts
        result = main(test_mode=True, testing=True)

        # Assert the result is a test commit message (simulation worked)
        self.assertIsNotNone(result)
        self.assertIn("[TEST MESSAGE]", result)

        # Verify prints were called for the test message
        mock_print.assert_any_call("\n=== Test Commit Message ===")
        mock_print.assert_any_call(result)

        # Verify we got simulation mode
        mock_run_subprocess.assert_not_called()

    def test_build_prompt_with_hint(self):
        """Test that the hint is properly incorporated into the prompt."""
        status = "M file1.py"
        diff = "diff --git a/file1.py b/file1.py\n+test content"
        hint = "JIRA-123"

        # Test with hint in regular mode
        prompt = build_prompt(status, diff, one_liner=False, hint=hint)
        self.assertIn("Please consider this context from the user: JIRA-123", prompt)

        # Test with hint in one-liner mode
        one_liner_prompt = build_prompt(status, diff, one_liner=True, hint=hint)
        self.assertIn("Please consider this context from the user: JIRA-123", one_liner_prompt)

        # Test without hint
        no_hint_prompt = build_prompt(status, diff, one_liner=False)
        self.assertNotIn("Please consider this context", no_hint_prompt)


if __name__ == "__main__":
    unittest.main()
