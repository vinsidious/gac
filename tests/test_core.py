"""Test module for gac.core."""

import logging
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from gac.core import build_prompt, main, run_subprocess, send_to_llm


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
        result = run_subprocess(["git", "status"])

        # Assert mock was called correctly
        mock_run.assert_called_once_with(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Assert result matches mock stdout
        assert result == "Command output"

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_failure(self, mock_run):
        """Test run_subprocess when command fails."""
        # Mock subprocess.run to return a failure result
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Command failed"
        mock_run.return_value = mock_process

        # Call run_subprocess and expect exception
        with pytest.raises(subprocess.CalledProcessError):
            run_subprocess(["git", "invalid"])

    def test_main_no_formatting(self, base_mocks):
        """Test main with formatting disabled."""
        # Call main with no_format=True
        result = main(no_format=True)

        # Assert commit message was generated and applied
        base_mocks["send_to_llm"].assert_called_once()
        base_mocks["commit_changes"].assert_called_once()
        assert result == "Generated commit message"

    @pytest.mark.parametrize(
        "mode",
        ["quiet", "verbose"],
    )
    def test_main_logging_modes(self, base_mocks, mode):
        """Test main in different logging modes."""
        # Call main with the specified mode
        kwargs = {mode: True}
        result = main(**kwargs)

        # We're only verifying that the function runs successfully with these modes
        # and that the commit was made
        base_mocks["commit_changes"].assert_called_once()
        assert result == "Generated commit message"

    def test_main_force_mode(self, base_mocks):
        """Test main in force mode."""
        # Call main in force mode
        result = main(force=True)

        # Assert prompt was not called (skipped confirmation)
        base_mocks["prompt"].assert_not_called()

        # Assert commit was made
        base_mocks["commit_changes"].assert_called_once()
        assert result == "Generated commit message"

    def test_main_model_override(self, base_mocks):
        """Test main with model override."""
        # Use patch.dict to mock os.environ
        with patch.dict("os.environ", {}, clear=True):
            # Call main with model override
            result = main(model="openai:gpt-4")

            # Check that the model was set in the environment
            import os

            assert os.environ.get("GAC_MODEL") == "openai:gpt-4"

            # Assert commit was made
            base_mocks["commit_changes"].assert_called_once()
            assert result == "Generated commit message"

    def test_main_add_all(self, base_mocks):
        """Test main with add_all option."""
        # Call main with add_all=True
        result = main(add_all=True)

        # Assert stage_files was called with ["."]
        base_mocks["stage_files"].assert_any_call(["."])

        # Assert commit was made
        base_mocks["commit_changes"].assert_called_once()
        assert result == "Generated commit message"

    def test_main_failed_llm(self, base_mocks):
        """Test main when LLM fails to generate a message."""
        # Setup mock to return None for send_to_llm
        base_mocks["send_to_llm"].return_value = None

        # Call main
        result = main()

        # Assert no commit was made
        base_mocks["commit_changes"].assert_not_called()
        assert result is None

    def test_main_user_declines_commit(self, base_mocks):
        """Test main when user declines to commit."""
        # Setup mock to return "n" for prompt
        base_mocks["prompt"].return_value = "n"

        # Call main
        result = main()

        # Assert no commit was made
        base_mocks["commit_changes"].assert_not_called()
        assert result is None

    def test_send_to_llm(self):
        """Test send_to_llm function."""
        with patch("gac.core.get_config") as mock_get_config:
            with patch("gac.core.count_tokens") as mock_count_tokens:
                with patch("gac.core.chat") as mock_chat:
                    # Setup mocks with required keys
                    mock_get_config.return_value = {
                        "model": "anthropic:claude-3-haiku",
                        "max_input_tokens": 1000,
                    }
                    mock_count_tokens.return_value = 100
                    mock_chat.return_value = "Generated commit message"

                    # Call send_to_llm
                    result = send_to_llm(
                        status="M file1.py",
                        diff="diff --git a/file1.py b/file1.py",
                        one_liner=False,
                    )

                    # Assert chat was called
                    mock_chat.assert_called_once()
                    assert result == "Generated commit message"

    def test_main_no_push(self, base_mocks):
        """Test main when user declines to push."""
        # Setup mocks for first prompt (commit) and second prompt (push)
        base_mocks["prompt"].side_effect = ["y", "n"]

        # Call main
        result = main()

        # Assert commit was made
        base_mocks["commit_changes"].assert_called_once()

        # Verify git push was not called
        for call_args in base_mocks["run_subprocess"].call_args_list:
            assert call_args[0][0] != ["git", "push"]

        assert result == "Generated commit message"

    def test_main_test_mode(self, mock_print, mock_get_staged_files, mock_run_subprocess):
        """Test main function in test mode."""
        # Mock staged files
        mock_get_staged_files.return_value = ["file1.py", "file2.py"]

        # Call main in test mode with testing=True to avoid interactive prompts
        result = main(test_mode=True, testing=True)

        # Assert the result is a test commit message
        assert result is not None
        assert "[TEST MESSAGE]" in result

        # Verify prints were called for the test message
        mock_print.assert_any_call("\n=== Test Commit Message ===")
        mock_print.assert_any_call(result)

        # Verify no subprocess calls for commit
        mock_run_subprocess.assert_not_called()

    def test_main_test_mode_with_real_diff(self):
        """Test main function in test mode with real diff option."""
        with patch("gac.core.get_staged_files") as mock_get_staged_files:
            with patch("gac.core.run_subprocess") as mock_run_subprocess:
                with patch("gac.core.build_prompt") as mock_build_prompt:
                    with patch("gac.core.count_tokens") as mock_count_tokens:
                        with patch("builtins.print"):
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
                            mock_count_tokens.return_value = 100

                            # Call main with test_with_real_diff option and testing=True to avoid interactive prompts
                            result = main(test_mode=True, test_with_real_diff=True, testing=True)

                            # Assert the result is a test commit message
                            assert result is not None

                            # Verify subprocess calls for status and diff
                            assert mock_run_subprocess.call_count >= 2
                            mock_run_subprocess.assert_any_call(["git", "status"])
                            mock_run_subprocess.assert_any_call(
                                ["git", "--no-pager", "diff", "--staged", "--patience"]
                            )

                            # Verify build_prompt was called
                            mock_build_prompt.assert_called_once()

    def test_main_empty_stage_test_mode(
        self, mock_print, mock_get_staged_files, mock_run_subprocess
    ):
        """Test main function with empty staging area in test mode."""
        # Mock empty staged files
        mock_get_staged_files.return_value = []

        # Call main in test mode
        result = main(test_mode=True, testing=True)

        # Assert the result is a test commit message
        assert result is not None
        assert "[TEST MESSAGE]" in result

        # Verify simulation mode was used
        mock_print.assert_any_call("\n=== Test Commit Message ===")

    def test_build_prompt_with_hint(self):
        """Test that the hint is properly incorporated into the prompt."""
        status = "M file1.py"
        diff = "diff --git a/file1.py b/file1.py\n+test content"
        hint = "JIRA-123"

        # Test with hint
        prompt = build_prompt(status, diff, one_liner=False, hint=hint)
        assert "Please consider this context from the user: JIRA-123" in prompt

        # Test with hint in one-liner mode
        one_liner_prompt = build_prompt(status, diff, one_liner=True, hint=hint)
        assert "Please consider this context from the user: JIRA-123" in one_liner_prompt

        # Test without hint
        no_hint_prompt = build_prompt(status, diff, one_liner=False)
        assert "Please consider this context" not in no_hint_prompt


if __name__ == "__main__":
    pytest.main()


# Add fixtures at the module level
@pytest.fixture(autouse=True)
def setup_mocks():
    """Set up common mocks for all tests."""
    with patch("gac.core.get_config") as mock_get_config:
        mock_get_config.return_value = {
            "model": "anthropic:claude-3-haiku",
            "use_formatting": True,
            "max_input_tokens": 1000,
        }
        with patch("gac.core.get_staged_files") as mock_get_staged_files:
            mock_get_staged_files.return_value = ["file1.py", "file2.txt"]
            with patch("gac.core.send_to_llm") as mock_send_to_llm:
                mock_send_to_llm.return_value = "Generated commit message"
                with patch("gac.core.stage_files") as mock_stage_files:
                    with patch("gac.core.run_subprocess") as mock_run_subprocess:
                        mock_run_subprocess.return_value = "Command output"
                        with patch("click.prompt") as mock_prompt:
                            mock_prompt.return_value = "y"
                            with patch("gac.core.commit_changes") as mock_commit_changes:
                                with patch("gac.core.count_tokens") as mock_count_tokens:
                                    mock_count_tokens.return_value = 100
                                    yield


@pytest.fixture
def base_mocks():
    """Fixture that provides all the common mocks for main() function tests."""
    with patch("gac.core.send_to_llm") as mock_send_to_llm:
        mock_send_to_llm.return_value = "Generated commit message"
        with patch("gac.core.commit_changes") as mock_commit_changes:
            with patch("gac.core.stage_files") as mock_stage_files:
                with patch("gac.core.run_subprocess") as mock_run_subprocess:
                    mock_run_subprocess.return_value = "Command output"
                    with patch("click.prompt") as mock_prompt:
                        mock_prompt.return_value = "y"
                        with patch("gac.core.get_staged_files") as mock_get_staged_files:
                            mock_get_staged_files.return_value = ["file1.py", "file2.txt"]
                            with patch("gac.core.get_config") as mock_get_config:
                                mock_get_config.return_value = {
                                    "model": "anthropic:claude-3-haiku",
                                    "use_formatting": True,
                                    "max_input_tokens": 1000,
                                }
                                yield {
                                    "send_to_llm": mock_send_to_llm,
                                    "commit_changes": mock_commit_changes,
                                    "stage_files": mock_stage_files,
                                    "run_subprocess": mock_run_subprocess,
                                    "prompt": mock_prompt,
                                    "get_staged_files": mock_get_staged_files,
                                    "get_config": mock_get_config,
                                }


@pytest.fixture
def mock_print():
    """Mock for builtins.print."""
    with patch("builtins.print") as mock:
        yield mock


@pytest.fixture
def mock_get_staged_files():
    """Mock for gac.core.get_staged_files."""
    with patch("gac.core.get_staged_files") as mock:
        mock.return_value = ["file1.py", "file2.txt"]
        yield mock


@pytest.fixture
def mock_run_subprocess():
    """Mock for gac.core.run_subprocess."""
    with patch("gac.core.run_subprocess") as mock:
        mock.return_value = "Command output"
        yield mock


@pytest.fixture
def mock_build_prompt():
    """Mock for gac.core.build_prompt."""
    with patch("gac.core.build_prompt") as mock:
        mock.return_value = "Test prompt"
        yield mock


@pytest.fixture
def mock_count_tokens():
    """Mock for gac.core.count_tokens."""
    with patch("gac.core.count_tokens") as mock:
        mock.return_value = 100
        yield mock
