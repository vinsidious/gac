"""Test module for gac.core."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from gac.core import build_prompt, create_abbreviated_prompt, main, send_to_llm
from gac.utils import run_subprocess


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
        # Setup mock to return "n" for click.prompt (declining the commit)
        base_mocks["prompt"].return_value = "n"

        # Call main
        main(test_mode=False, force=False, testing=False)

        # Assert no commit was made
        base_mocks["commit_changes"].assert_not_called()

    def test_send_to_llm(self):
        """Test send_to_llm function."""
        with patch("gac.core.get_config") as mock_get_config:
            with patch("gac.core.count_tokens") as mock_count_tokens:
                with patch("gac.core.chat") as mock_chat:
                    # Setup mocks with required keys
                    mock_get_config.return_value = {
                        "model": "anthropic:claude-3-haiku",
                        "warning_limit_input_tokens": 1000,
                        "max_output_tokens": 512,
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
        # Setup mocks for first confirmation (commit) and second confirmation (push)
        base_mocks["confirm"].return_value = True  # Confirm all other prompts

        # First prompt is for commit, second is for push
        base_mocks["prompt"].side_effect = ["y", "n"]

        # Call main with normal mode
        main(test_mode=False, force=False, testing=False)

        # Check push not called
        push_called = False
        for call_args in base_mocks["run_subprocess"].call_args_list:
            if call_args[0][0] == ["git", "push"]:
                push_called = True
                break

        assert not push_called, "Git push should not have been called"

    @patch("gac.core.get_staged_files")
    @patch("gac.core.run_subprocess")
    @patch("gac.core.send_to_llm")
    def test_main_test_mode(self, mock_send_to_llm, mock_run_subprocess, mock_get_staged_files):
        """Test main function in test mode."""
        # Mock staged files
        mock_get_staged_files.return_value = ["file1.py", "file2.py"]

        # Mock send_to_llm to return a test message
        mock_send_to_llm.return_value = "Test commit message"

        # Call main in test mode with testing=True to avoid interactive prompts
        result = main(test_mode=True, testing=True)

        # Assert the result is the test commit message
        assert result is not None
        assert result == "Test commit message"

    def test_main_test_mode_with_real_diff(self):
        """Test main function in test mode with real diff option."""
        with patch("gac.core.get_staged_files") as mock_get_staged_files:
            with patch("gac.core.run_subprocess") as mock_run_subprocess:
                with patch("gac.core.send_to_llm") as mock_send_to_llm:
                    with patch("gac.core.get_staged_diff") as mock_get_staged_diff:
                        # Mock staged files
                        mock_get_staged_files.return_value = ["file1.py", "file2.py"]

                        # Mock subprocess calls for git status
                        mock_run_subprocess.return_value = "M file1.py\nA file2.py"

                        # Mock get_staged_diff
                        mock_get_staged_diff.return_value = (
                            "diff --git a/file1.py b/file1.py\n+test content",
                            [],
                        )

                        # Mock send_to_llm to return a test message
                        mock_send_to_llm.return_value = "Test commit message"

                        # Call main with test_with_real_diff option and testing=True to avoid
                        # interactive prompts
                        result = main(test_mode=True, test_with_real_diff=True, testing=True)

                        # Assert the result is the test commit message
                        assert result is not None
                        assert result == "Test commit message"

                        # Verify subprocess calls for status
                        mock_run_subprocess.assert_called_with(["git", "status"])

    @patch("gac.core.get_staged_files")
    @patch("gac.core.run_subprocess")
    @patch("gac.core.send_to_llm")
    def test_main_empty_stage_test_mode(
        self, mock_send_to_llm, mock_run_subprocess, mock_get_staged_files
    ):
        """Test main function with empty staging area in test mode."""
        # Mock empty staged files
        mock_get_staged_files.return_value = []

        # Mock send_to_llm to return a test message
        mock_send_to_llm.return_value = "Test commit message"

        # Call main in test mode
        result = main(test_mode=True, testing=True)

        # Assert the result is the test commit message
        assert result is not None
        assert result == "Test commit message"

    def test_build_prompt_with_hint(self):
        """Test that the hint is included in the prompt."""
        status = "M file1.py"
        diff = "diff --git a/file1.py b/file1.py"
        hint = "This fixes issue #123"

        prompt = build_prompt(status, diff, one_liner=False, hint=hint)

        assert "Please consider this context from the user: This fixes issue #123" in prompt
        assert "Current git status:" in prompt
        assert "Changes to be committed:" in prompt
        assert status in prompt
        assert diff in prompt

    def test_build_prompt_conventional_format(self):
        """Test that the conventional commit format instructions are included in the prompt."""
        status = "M file1.py\nM file2.py"
        diff = "diff --git a/file1.py b/file1.py\n+new line"

        prompt = build_prompt(status, diff, conventional=True)

        # Check for conventional commit format instructions
        assert (
            "Use the Conventional Commits format: <type>(<optional scope>): <description>" in prompt
        )
        assert "feat: A new feature" in prompt
        assert "fix: A bug fix" in prompt
        assert "docs: Documentation changes" in prompt
        assert "style: Changes that don't affect code meaning" in prompt
        assert "refactor: Code changes that neither fix a bug nor add a feature" in prompt
        assert "perf: Performance improvements" in prompt
        assert "test: Adding or correcting tests" in prompt

        # Make sure all common types are included
        assert "build:" in prompt
        assert "ci:" in prompt
        assert "chore:" in prompt

        # Check for breaking changes instructions
        assert "BREAKING CHANGE:" in prompt

        # Standard prompt elements should still be present
        assert "Current git status:" in prompt
        assert "Changes to be committed:" in prompt
        assert status in prompt
        assert diff in prompt

    def test_create_abbreviated_prompt(self):
        """Test that the create_abbreviated_prompt function correctly abbreviates diffs."""
        # Create a prompt with a large diff
        status = "M file1.py"
        diff_lines = ["diff --git a/file1.py b/file1.py"]
        # Add 100 lines to the diff
        for i in range(1, 101):
            diff_lines.append(f"+line {i}")
        diff = "\n".join(diff_lines)

        # Build the full prompt
        full_prompt = build_prompt(status, diff)

        # Create the abbreviated prompt
        abbreviated_prompt = create_abbreviated_prompt(full_prompt, max_diff_lines=20)

        # Verify it contains the expected elements
        assert "lines hidden" in abbreviated_prompt
        assert "Use --show-prompt-full" in abbreviated_prompt

        # Make sure it contains some beginning and ending lines
        assert "+line 1" in abbreviated_prompt
        assert "+line 100" in abbreviated_prompt

        # The abbreviated prompt should be shorter than the full prompt
        assert len(abbreviated_prompt) < len(full_prompt)


if __name__ == "__main__":
    pytest.main()


@pytest.fixture(autouse=True)
def setup_mocks():
    """Set up common mocks for all tests."""
    with patch("gac.core.get_config") as mock_get_config:
        mock_get_config.return_value = {
            "model": "anthropic:claude-3-haiku",
            "use_formatting": True,
            "warning_limit_input_tokens": 1000,
        }
        with patch("gac.core.get_staged_files") as mock_get_staged_files:
            mock_get_staged_files.return_value = ["file1.py", "file2.txt"]
            with patch("gac.core.send_to_llm") as mock_send_to_llm:
                mock_send_to_llm.return_value = "Generated commit message"
                with patch("gac.core.run_subprocess") as mock_run_subprocess:
                    mock_run_subprocess.return_value = "Command output"
                    with patch("click.prompt") as mock_prompt:
                        mock_prompt.return_value = "y"
                        with patch("gac.core.count_tokens") as mock_count_tokens:
                            mock_count_tokens.return_value = 100
                            yield


@pytest.fixture
def base_mocks():
    """Set up base mocks for all commit tests."""
    with (
        patch("gac.core.send_to_llm") as mock_send_to_llm,
        patch("gac.core.commit_changes") as mock_commit,
        patch("gac.core.stage_files") as mock_stage_files,
        patch("gac.core.get_staged_files") as mock_get_staged_files,
        patch("gac.core.get_staged_diff") as mock_get_staged_diff,
        patch("gac.formatting.format_staged_files") as mock_format_staged_files,
        patch("gac.core.run_subprocess") as mock_run_subprocess,
        patch("gac.core.get_config") as mock_get_config,
        patch("click.confirm") as mock_confirm,
        patch("click.prompt") as mock_prompt,
    ):
        # Set up mock responses
        mock_send_to_llm.return_value = "Generated commit message"
        mock_get_staged_files.return_value = ["file1.py", "file2.md"]
        mock_get_staged_diff.return_value = (
            "diff content",
            [],
        )  # Return diff and list of truncated files
        mock_format_staged_files.return_value = (True, [".py", ".md"])
        mock_get_config.return_value = {
            "model": "test-model",
            "push_after_commit": False,
            "use_formatting": True,
        }
        mock_confirm.return_value = True
        mock_prompt.return_value = "y"  # Default to 'yes' for prompts

        # Yield all mocks for use in tests
        yield {
            "send_to_llm": mock_send_to_llm,
            "commit_changes": mock_commit,
            "stage_files": mock_stage_files,
            "get_staged_files": mock_get_staged_files,
            "get_staged_diff": mock_get_staged_diff,
            "format_staged_files": mock_format_staged_files,
            "run_subprocess": mock_run_subprocess,
            "get_config": mock_get_config,
            "confirm": mock_confirm,
            "prompt": mock_prompt,
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
