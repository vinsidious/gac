"""Extended tests for init_cli module to improve coverage."""

import tempfile
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from gac.init_cli import init


def test_init_cli_creates_new_gac_env_file():
    """Test that init creates .gac.env if it doesn't exist."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Don't create the file beforehand
        assert not env_path.exists()

        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["Anthropic", "English"]
                mtext.return_value.ask.side_effect = ["claude-sonnet-4-5"]
                mpass.return_value.ask.side_effect = ["test-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert env_path.exists()
                assert f"Created $HOME/.gac.env at {env_path}" in result.output


def test_init_cli_custom_anthropic_with_default_version():
    """Test Custom (Anthropic) provider configuration with default API version."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["Custom (Anthropic)", "English"]
                # Text prompts: model (required), base URL (required), API version (optional)
                mtext.return_value.ask.side_effect = [
                    "claude-4-haiku",  # model
                    "https://custom-anthropic.example.com",  # base URL
                    "2023-06-01",  # default version (should not be saved)
                ]
                mpass.return_value.ask.side_effect = ["custom-api-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='custom-anthropic:claude-4-haiku'" in env_text
                assert "CUSTOM_ANTHROPIC_BASE_URL='https://custom-anthropic.example.com'" in env_text
                assert "CUSTOM_ANTHROPIC_API_KEY='custom-api-key'" in env_text
                # Default version should not be saved
                assert "CUSTOM_ANTHROPIC_VERSION" not in env_text


def test_init_cli_custom_anthropic_with_custom_version():
    """Test Custom (Anthropic) provider configuration with custom API version."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["Custom (Anthropic)", "English"]
                mtext.return_value.ask.side_effect = [
                    "claude-4-opus",
                    "https://custom.api.com",
                    "2024-01-01",  # custom version
                ]
                mpass.return_value.ask.side_effect = ["key123"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "CUSTOM_ANTHROPIC_VERSION='2024-01-01'" in env_text


def test_init_cli_custom_anthropic_base_url_cancelled():
    """Test Custom (Anthropic) cancellation when base URL is cancelled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
            ):
                mselect.return_value.ask.return_value = "Custom (Anthropic)"
                # Model then base URL (cancelled)
                mtext.return_value.ask.side_effect = ["claude-4", None]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Custom Anthropic base URL entry cancelled" in result.output


def test_init_cli_custom_openai_configuration():
    """Test Custom (OpenAI) provider configuration."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["Custom (OpenAI)", "English"]
                mtext.return_value.ask.side_effect = [
                    "gpt-oss-20b",  # model
                    "https://custom-openai.example.com/v1",  # base URL
                ]
                mpass.return_value.ask.side_effect = ["custom-openai-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='custom-openai:gpt-oss-20b'" in env_text
                assert "CUSTOM_OPENAI_BASE_URL='https://custom-openai.example.com/v1'" in env_text
                assert "CUSTOM_OPENAI_API_KEY='custom-openai-key'" in env_text


def test_init_cli_custom_openai_base_url_cancelled():
    """Test Custom (OpenAI) cancellation when base URL is cancelled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
            ):
                mselect.return_value.ask.return_value = "Custom (OpenAI)"
                mtext.return_value.ask.side_effect = ["gpt-model", None]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Custom OpenAI base URL entry cancelled" in result.output


def test_init_cli_empty_model_suggestion():
    """Test providers with empty model suggestions (require explicit model entry)."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Custom providers have empty model suggestions
                mselect.return_value.ask.side_effect = ["Custom (OpenAI)", "English"]
                mtext.return_value.ask.side_effect = [
                    "my-custom-model",  # model (required, no default)
                    "https://example.com/v1",  # base URL
                ]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                # Verify the model was set correctly (proving the prompt worked)
                env_text = env_path.read_text()
                assert "GAC_MODEL='custom-openai:my-custom-model'" in env_text


def test_init_cli_lmstudio_with_api_key():
    """Test LM Studio configuration with an API key provided."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["LM Studio", "English"]
                mtext.return_value.ask.side_effect = ["gemma3", "http://localhost:1234"]
                mpass.return_value.ask.side_effect = ["lmstudio-key-123"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "LMSTUDIO_API_KEY='lmstudio-key-123'" in env_text
                assert "Skipping API key" not in result.output


def test_init_cli_language_selection_cancelled():
    """Test behavior when language selection is cancelled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language cancelled (None)
                mselect.return_value.ask.side_effect = ["Anthropic", None]
                mtext.return_value.ask.side_effect = ["claude-sonnet-4-5"]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Language selection cancelled. Using English (default)" in result.output


def test_init_cli_custom_language_selection():
    """Test selecting a custom language during init."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider, Custom language, Prefix choice
                mselect.return_value.ask.side_effect = [
                    "Anthropic",
                    "Custom",  # Custom language
                    "Keep prefixes in English (feat:, fix:, etc.)",
                ]
                mtext.return_value.ask.side_effect = [
                    "claude-sonnet-4-5",  # model
                    "Esperanto",  # custom language name
                ]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_LANGUAGE='Esperanto'" in env_text
                assert "GAC_TRANSLATE_PREFIXES='false'" in env_text


def test_init_cli_custom_language_empty_input():
    """Test custom language with empty input falls back to English."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["Anthropic", "Custom"]
                mtext.return_value.ask.side_effect = [
                    "claude-sonnet-4-5",
                    "",  # empty custom language
                ]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "No language entered. Using English (default)" in result.output
                env_text = env_path.read_text()
                # Language should not be set
                assert "GAC_LANGUAGE" not in env_text


def test_init_cli_custom_language_whitespace_only():
    """Test custom language with whitespace-only input falls back to English."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = ["Anthropic", "Custom"]
                mtext.return_value.ask.side_effect = ["claude-sonnet-4-5", "   "]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "No language entered. Using English (default)" in result.output


def test_init_cli_predefined_language_with_prefix_translation():
    """Test selecting a predefined language with prefix translation."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = [
                    "Anthropic",
                    "Español",  # Spanish
                    "Translate prefixes into Spanish",
                ]
                mtext.return_value.ask.side_effect = ["claude-sonnet-4-5"]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_LANGUAGE='Spanish'" in env_text
                assert "GAC_TRANSLATE_PREFIXES='true'" in env_text


def test_init_cli_predefined_language_keep_english_prefixes():
    """Test selecting a predefined language but keeping English prefixes."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = [
                    "Anthropic",
                    "日本語",  # Japanese
                    "Keep prefixes in English (feat:, fix:, etc.)",
                ]
                mtext.return_value.ask.side_effect = ["claude-sonnet-4-5"]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_LANGUAGE='Japanese'" in env_text
                assert "GAC_TRANSLATE_PREFIXES='false'" in env_text


def test_init_cli_prefix_translation_cancelled():
    """Test behavior when prefix translation choice is cancelled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        env_path.touch()
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.side_effect = [
                    "Anthropic",
                    "Français",  # French
                    None,  # Cancel prefix choice
                ]
                mtext.return_value.ask.side_effect = ["claude-sonnet-4-5"]
                mpass.return_value.ask.side_effect = ["key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Prefix translation selection cancelled. Using English prefixes" in result.output
                env_text = env_path.read_text()
                # Language should still be set, with prefixes defaulting to false
                assert "GAC_LANGUAGE='French'" in env_text
                assert "GAC_TRANSLATE_PREFIXES='false'" in env_text


def test_init_cli_multiple_predefined_languages():
    """Test that various predefined languages map correctly."""
    test_cases = [
        ("简体中文", "Simplified Chinese"),
        ("繁體中文", "Traditional Chinese"),
        ("한국어", "Korean"),
        ("Português", "Portuguese"),
        ("Русский", "Russian"),
    ]

    for display_name, english_name in test_cases:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".gac.env"
            env_path.touch()
            with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
                with (
                    mock.patch("questionary.select") as mselect,
                    mock.patch("questionary.text") as mtext,
                    mock.patch("questionary.password") as mpass,
                ):
                    mselect.return_value.ask.side_effect = [
                        "Anthropic",
                        display_name,
                        "Keep prefixes in English (feat:, fix:, etc.)",
                    ]
                    mtext.return_value.ask.side_effect = ["claude-sonnet-4-5"]
                    mpass.return_value.ask.side_effect = ["key"]

                    result = runner.invoke(init)
                    assert result.exit_code == 0
                    env_text = env_path.read_text()
                    assert f"GAC_LANGUAGE='{english_name}'" in env_text
