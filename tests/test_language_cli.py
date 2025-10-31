"""Tests for language_cli module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from gac.language_cli import language


def test_language_select_predefined_with_prefix_translation():
    """Test selecting a predefined language with prefix translation enabled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            # Mock questionary to select Spanish and translate prefixes
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Español",  # Language selection
                    "Translate prefixes into Spanish",  # Prefix choice
                ]
                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to Español" in result.output
                assert "GAC_LANGUAGE=Spanish" in result.output
                assert "GAC_TRANSLATE_PREFIXES=true" in result.output
                assert "Prefixes will be translated" in result.output
                assert fake_path.exists()

                # Verify the file contents
                content = fake_path.read_text()
                assert "GAC_LANGUAGE=" in content and "Spanish" in content
                assert "GAC_TRANSLATE_PREFIXES=" in content and "true" in content


def test_language_select_predefined_without_prefix_translation():
    """Test selecting a predefined language without prefix translation."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "日本語",  # Japanese
                    "Keep prefixes in English (feat:, fix:, etc.)",  # Keep English prefixes
                ]
                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to 日本語" in result.output
                assert "GAC_LANGUAGE=Japanese" in result.output
                assert "GAC_TRANSLATE_PREFIXES=false" in result.output
                assert "Prefixes will remain in English" in result.output
                assert fake_path.exists()

                content = fake_path.read_text()
                assert "GAC_LANGUAGE=" in content and "Japanese" in content
                assert "GAC_TRANSLATE_PREFIXES=" in content and "false" in content


def test_language_select_english_removes_setting():
    """Test selecting English removes the language setting."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"

        # Pre-populate .gac.env with a language setting
        fake_path.write_text("GAC_LANGUAGE=Spanish\nGAC_TRANSLATE_PREFIXES=true\n")

        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.return_value = "English"

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to English (default)" in result.output
                assert "Removed GAC_LANGUAGE" in result.output

                # Verify GAC_LANGUAGE was removed from file
                content = fake_path.read_text()
                assert "GAC_LANGUAGE" not in content


def test_language_select_english_file_not_exists():
    """Test selecting English when .gac.env doesn't exist yet."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"

        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.return_value = "English"

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to English (default)" in result.output
                # File should be created even for English
                assert fake_path.exists()


def test_language_select_custom_language():
    """Test selecting a custom language."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.side_effect = [
                    "Custom",  # Language selection
                    "Keep prefixes in English (feat:, fix:, etc.)",  # Prefix choice
                ]
                mock_text.return_value.ask.return_value = "Esperanto"

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to Custom" in result.output
                assert "GAC_LANGUAGE=Esperanto" in result.output
                assert fake_path.exists()

                content = fake_path.read_text()
                assert "GAC_LANGUAGE=" in content and "Esperanto" in content


def test_language_select_custom_with_whitespace():
    """Test selecting a custom language with leading/trailing whitespace."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.side_effect = [
                    "Custom",
                    "Keep prefixes in English (feat:, fix:, etc.)",
                ]
                mock_text.return_value.ask.return_value = "  Klingon  "

                result = runner.invoke(language)

                assert result.exit_code == 0
                # Should be trimmed
                assert "GAC_LANGUAGE=Klingon" in result.output


def test_language_custom_cancelled_empty_input():
    """Test cancelling custom language with empty input."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.return_value = "Custom"
                mock_text.return_value.ask.return_value = ""

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "No language entered. Cancelled." in result.output
                # File might be created but shouldn't have language set
                if fake_path.exists():
                    content = fake_path.read_text()
                    assert "GAC_LANGUAGE" not in content


def test_language_custom_cancelled_whitespace_only():
    """Test cancelling custom language with whitespace-only input."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.return_value = "Custom"
                mock_text.return_value.ask.return_value = "   "

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "No language entered. Cancelled." in result.output


def test_language_custom_cancelled_none():
    """Test cancelling custom language with None (Ctrl+C)."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.return_value = "Custom"
                mock_text.return_value.ask.return_value = None

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "No language entered. Cancelled." in result.output


def test_language_selection_cancelled():
    """Test cancelling at the language selection step."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.return_value = None  # User pressed Ctrl+C

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "Language selection cancelled." in result.output


def test_language_prefix_selection_cancelled():
    """Test cancelling at the prefix translation selection step."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Français",  # Language selection
                    None,  # Cancel prefix selection
                ]

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "Prefix translation selection cancelled." in result.output
                # File might be created but language should not be saved if prefix selection was cancelled


def test_language_creates_file_if_not_exists():
    """Test that .gac.env is created if it doesn't exist."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"

        # Ensure file doesn't exist
        assert not fake_path.exists()

        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Português",
                    "Keep prefixes in English (feat:, fix:, etc.)",
                ]

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert f"Created {fake_path}" in result.output
                assert fake_path.exists()


def test_language_all_predefined_languages():
    """Test that all predefined languages can be selected and stored correctly."""
    runner = CliRunner()

    test_languages = [
        ("简体中文", "Simplified Chinese"),
        ("繁體中文", "Traditional Chinese"),
        ("한국어", "Korean"),
        ("Deutsch", "German"),
        ("Русский", "Russian"),
        ("हिन्दी", "Hindi"),
        ("العربية", "Arabic"),
        ("עברית", "Hebrew"),
    ]

    for display_name, english_name in test_languages:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / ".gac.env"
            with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
                with patch("questionary.select") as mock_select:
                    mock_select.return_value.ask.side_effect = [
                        display_name,
                        "Keep prefixes in English (feat:, fix:, etc.)",
                    ]

                    result = runner.invoke(language)

                    assert result.exit_code == 0
                    assert f"✓ Set language to {display_name}" in result.output
                    assert f"GAC_LANGUAGE={english_name}" in result.output

                    content = fake_path.read_text()
                    assert "GAC_LANGUAGE=" in content and english_name in content


def test_language_display_shows_instructions():
    """Test that the command displays initial instructions."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.return_value = None  # Cancel immediately

                result = runner.invoke(language)

                assert "Select a language for your commit messages:" in result.output


def test_language_existing_file_is_updated():
    """Test that selecting a new language updates existing .gac.env file."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"

        # Pre-populate with existing config
        fake_path.write_text("GAC_MODEL=anthropic:claude-3-haiku\nGAC_LANGUAGE=Spanish\n")

        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Français",
                    "Translate prefixes into French",
                ]

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to Français" in result.output

                content = fake_path.read_text()
                # Should update language but preserve other settings
                assert "GAC_MODEL=anthropic:claude-3-haiku" in content
                assert "GAC_LANGUAGE=" in content and "French" in content
                assert "Spanish" not in content
                assert "GAC_TRANSLATE_PREFIXES=" in content and "true" in content


def test_language_prefix_translation_message_shows_language_name():
    """Test that prefix translation message shows the selected language name."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.language_cli.GAC_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Italiano",
                    "Translate prefixes into Italian",
                ]

                result = runner.invoke(language)

                assert result.exit_code == 0
                # The prefix choice message should mention "Italian"
                assert (
                    "Translate prefixes into Italian" in result.output or "GAC_TRANSLATE_PREFIXES=true" in result.output
                )
