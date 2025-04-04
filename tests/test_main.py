from unittest.mock import patch

from click.testing import CliRunner

from gac.config import Config
from gac.main import main


@patch("gac.config.run_config_wizard")
def test_main_config_option(mock_wizard):
    """Test the config option in main function."""
    # Setup mock
    mock_wizard.return_value = Config(
        model="anthropic:test-model",
        use_formatting=True,
        max_output_tokens=256,
        warning_limit_input_tokens=16000,
        api_key="test-api-key",
    )

    # Run test
    runner = CliRunner()
    result = runner.invoke(main, ["--config"])

    # Verify
    assert result.exit_code == 0
    assert mock_wizard.called
    assert "Configuration saved successfully!" in result.output


@patch("gac.config.run_config_wizard")
def test_main_log_level_options(mock_wizard):
    """Test different log level options."""
    # Setup mock
    mock_wizard.return_value = Config(
        model="anthropic:test-model",
        use_formatting=True,
        max_output_tokens=256,
        warning_limit_input_tokens=16000,
        api_key="test-api-key",
    )

    runner = CliRunner()
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

    for level in log_levels:
        result = runner.invoke(main, ["--log-level", level, "--config"])
        assert result.exit_code == 0
        assert mock_wizard.called
        assert "Configuration saved successfully!" in result.output
        mock_wizard.reset_mock()


# Mock both commit_workflow and setup_logging to avoid actual logging configuration
@patch("gac.main.setup_logging")
@patch("gac.main.commit_workflow")
def test_main_cli_options(mock_commit_workflow, mock_setup_logging):
    """Test various CLI options without executing actual git commands."""
    # Setup mock to return success
    mock_commit_workflow.return_value = {
        "success": True,
        "message": "Test commit message",
        "pushed": False,
    }

    runner = CliRunner(mix_stderr=False)
    options_to_test = [
        ["--quiet"],  # Start with simple option
        ["--force"],
        ["--no-format"],
        ["--one-liner"],
        ["--model", "test:model"],
    ]

    for opts in options_to_test:
        result = runner.invoke(main, opts)
        assert result.exit_code == 0, f"Failed with options: {opts}"
        assert mock_commit_workflow.called
        mock_commit_workflow.reset_mock()


# Mock both commit_workflow and setup_logging
@patch("gac.main.setup_logging")
@patch("gac.main.commit_workflow")
def test_main_error_handling(mock_commit_workflow, mock_setup_logging):
    """Test error handling in main."""
    # Setup mock to return error
    mock_commit_workflow.return_value = {"success": False, "error": "Test error message"}

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["--quiet"])  # Adding --quiet to minimize output

    # Should exit with code 1 on error
    assert result.exit_code == 1
    assert mock_commit_workflow.called
    assert "Test error message" in result.output
