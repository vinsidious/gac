"""Test module for gac.config."""

import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

from gac.config import (
    DEFAULT_CONFIG,
    PROVIDER_MODELS,
    ConfigError,
    get_config,
    run_config_wizard,
    validate_config,
)


class TestConfig(unittest.TestCase):
    """Tests for configuration settings."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Store original environment variables
        self.original_env = os.environ.copy()

        # Clear environment variables that might affect tests
        for var in [
            "GAC_MODEL",
            "GAC_PROVIDER",
            "GAC_MODEL_NAME",
            "GAC_USE_FORMATTING",
            "GAC_MAX_OUTPUT_TOKENS",
        ]:
            if var in os.environ:
                del os.environ[var]

    def tearDown(self):
        """Tear down test fixtures after each test."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_default_config(self):
        """Test that get_config returns default configuration when no env vars are set."""
        # Call get_config
        config = get_config()

        # Create a copy of the config without api_key for comparison
        config_without_api_key = {k: v for k, v in config.items() if k != "api_key"}

        # Assert default values are returned (ignoring api_key)
        self.assertEqual(config_without_api_key, DEFAULT_CONFIG)
        self.assertEqual(config["model"], DEFAULT_CONFIG["model"])
        self.assertTrue(config["use_formatting"])
        self.assertEqual(config["max_output_tokens"], DEFAULT_CONFIG["max_output_tokens"])

    def test_gac_model_with_provider(self):
        """Test that GAC_MODEL with provider prefix works correctly."""
        # Set GAC_MODEL with provider prefix
        os.environ["GAC_MODEL"] = "openai:gpt-4o-mini"

        # Call get_config
        config = get_config()

        # Assert config uses provided model
        self.assertEqual(config["model"], "openai:gpt-4o-mini")

        # Other settings should remain default
        self.assertEqual(config["use_formatting"], DEFAULT_CONFIG["use_formatting"])
        self.assertEqual(config["max_output_tokens"], DEFAULT_CONFIG["max_output_tokens"])

    def test_unknown_provider_fallback(self):
        """Test that an unknown provider falls back to anthropic with its default model."""
        # Set an unknown provider
        os.environ["GAC_PROVIDER"] = "unknown_provider"

        # Call get_config
        config = get_config()

        # Assert fallback to anthropic with its default model
        expected_model = f"anthropic:{PROVIDER_MODELS['anthropic']}"
        self.assertEqual(config["model"], expected_model)

    def test_gac_use_formatting_true(self):
        """Test that GAC_USE_FORMATTING=true sets use_formatting to True."""
        os.environ["GAC_USE_FORMATTING"] = "true"
        config = get_config()
        self.assertTrue(config["use_formatting"])

    def test_gac_use_formatting_false(self):
        """Test that GAC_USE_FORMATTING=false sets use_formatting to False."""
        os.environ["GAC_USE_FORMATTING"] = "false"
        config = get_config()
        self.assertFalse(config["use_formatting"])

    def test_gac_use_formatting_invalid(self):
        """Test that invalid GAC_USE_FORMATTING value defaults to True."""
        os.environ["GAC_USE_FORMATTING"] = "invalid"
        config = get_config()
        self.assertFalse(
            config["use_formatting"]
        )  # Should be False because "invalid".lower() != "true"

    def test_gac_max_output_tokens_valid(self):
        """Test that valid GAC_MAX_OUTPUT_TOKENS value is used."""
        os.environ["GAC_MAX_OUTPUT_TOKENS"] = "4096"
        config = get_config()
        self.assertEqual(config["max_output_tokens"], 4096)

    def test_gac_max_output_tokens_invalid(self):
        """Test that invalid GAC_MAX_OUTPUT_TOKENS value is ignored."""
        os.environ["GAC_MAX_OUTPUT_TOKENS"] = "not_a_number"
        config = get_config()
        self.assertEqual(config["max_output_tokens"], DEFAULT_CONFIG["max_output_tokens"])


def test_config_wizard_provider_selection():
    """Test that the configuration wizard allows selecting a provider."""
    mock_select = MagicMock()
    mock_select.ask.side_effect = ["anthropic", "claude-3-5-haiku-latest"]
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        with patch("questionary.select", return_value=mock_select):
            with patch("questionary.confirm", return_value=mock_confirm):
                config = run_config_wizard()

                assert config is not None
                assert config["model"].startswith("anthropic:")
                assert validate_config(config)


def test_config_wizard_cancellation():
    """Test that the configuration wizard can be cancelled."""
    mock_select = MagicMock()
    mock_select.ask.return_value = None

    with patch("questionary.select", return_value=mock_select):
        config = run_config_wizard()
        assert config is None


def test_config_wizard_validation():
    """Test configuration validation for wizard-generated configs."""
    mock_select = MagicMock()
    mock_select.ask.side_effect = ["anthropic", "claude-3-5-haiku-latest"]
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        with patch("questionary.select", return_value=mock_select):
            with patch("questionary.confirm", return_value=mock_confirm):
                config = run_config_wizard()

                assert config is not None
                try:
                    validate_config(config)
                except ConfigError as e:
                    pytest.fail(f"Configuration validation failed: {e}")


def test_config_wizard_formatting_option():
    """Test that the formatting option can be toggled."""
    mock_select = MagicMock()
    mock_select.ask.side_effect = [
        "anthropic",
        "claude-3-5-haiku-latest",
        "anthropic",
        "claude-3-5-haiku-latest",
    ]
    mock_confirm = MagicMock()
    mock_confirm.ask.side_effect = [False, True, True, True]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        with patch("questionary.select", return_value=mock_select):
            with patch("questionary.confirm", return_value=mock_confirm):
                # First config with formatting disabled
                config1 = run_config_wizard()
                assert config1 is not None
                assert config1["use_formatting"] is False

                # Second config with formatting enabled
                config2 = run_config_wizard()
                assert config2 is not None
                assert config2["use_formatting"] is True


def test_config_wizard_model_selection():
    """Test that different models can be selected for each provider."""
    providers_and_models = {
        "anthropic": ["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
        "openai": ["gpt-4o-mini", "gpt-4o"],
        "groq": ["llama3-70b-8192", "mixtral-8x7b-32768"],
        "mistral": ["mistral-large-latest", "mistral-medium-latest"],
    }

    # Set up mock API keys
    env_vars = {
        "ANTHROPIC_API_KEY": "test_key",
        "OPENAI_API_KEY": "test_key",
        "GROQ_API_KEY": "test_key",
        "MISTRAL_API_KEY": "test_key",
    }

    with patch.dict(os.environ, env_vars):
        for provider, models in providers_and_models.items():
            for model in models:
                mock_select = MagicMock()
                mock_select.ask.side_effect = [provider, model]
                mock_confirm = MagicMock()
                mock_confirm.ask.return_value = True

                with patch("questionary.select", return_value=mock_select):
                    with patch("questionary.confirm", return_value=mock_confirm):
                        config = run_config_wizard()

                        assert config is not None
                        assert config["model"] == f"{provider}:{model}"
                        assert validate_config(config)


if __name__ == "__main__":
    unittest.main()
