"""Test module for gac.config."""

import os
import unittest
from unittest.mock import MagicMock, patch

from gac.config import DEFAULT_CONFIG, Config, get_config, run_config_wizard


class TestConfig(unittest.TestCase):
    """Tests for configuration settings."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Store original environment variables
        self.original_env = os.environ.copy()

        # Clear environment variables that might affect tests
        for var in [
            "GAC_MODEL",
            "GAC_USE_FORMATTING",
            "GAC_MAX_OUTPUT_TOKENS",
        ]:
            if var in os.environ:
                del os.environ[var]

        # Add mock API keys for testing
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        os.environ["OPENAI_API_KEY"] = "test_key"
        os.environ["GROQ_API_KEY"] = "test_key"
        os.environ["MISTRAL_API_KEY"] = "test_key"

    def tearDown(self):
        """Tear down test fixtures after each test."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_default_config(self):
        """Test that get_config returns default configuration when no env vars are set."""
        # Call get_config with no environment variables set
        config = get_config()

        # Verify the behavior: default configuration is returned
        self.assertEqual(config.model, DEFAULT_CONFIG["model"])
        self.assertEqual(config.use_formatting, DEFAULT_CONFIG["use_formatting"])
        self.assertEqual(config.max_output_tokens, DEFAULT_CONFIG["max_output_tokens"])

    def test_gac_model_with_provider(self):
        """Test that environment variable GAC_MODEL with provider prefix is properly recognized."""
        # Set GAC_MODEL with provider prefix
        os.environ["GAC_MODEL"] = "openai:gpt-4o-mini"

        # Call get_config
        config = get_config()

        # Verify the behavior: config uses the specified model
        self.assertEqual(config.model, "openai:gpt-4o-mini")

    def test_gac_use_formatting_true(self):
        """Test that GAC_USE_FORMATTING=true enables formatting."""
        # Set environment variable
        os.environ["GAC_USE_FORMATTING"] = "true"

        # Call get_config
        config = get_config()

        # Verify the behavior: formatting is enabled
        self.assertTrue(config.use_formatting)

    def test_gac_use_formatting_false(self):
        """Test that GAC_USE_FORMATTING=false disables formatting."""
        # Set environment variable
        os.environ["GAC_USE_FORMATTING"] = "false"

        # Call get_config
        config = get_config()

        # Verify the behavior: formatting is disabled
        self.assertFalse(config.use_formatting)

    def test_gac_use_formatting_invalid(self):
        """Test that invalid GAC_USE_FORMATTING value has expected behavior."""
        # Set invalid environment variable
        os.environ["GAC_USE_FORMATTING"] = "invalid"

        # Call get_config
        config = get_config()

        # Verify the behavior: invalid value is interpreted as False
        self.assertFalse(config.use_formatting)

    def test_gac_max_output_tokens_valid(self):
        """Test that valid GAC_MAX_OUTPUT_TOKENS value is properly applied."""
        # Set environment variable with valid token count
        os.environ["GAC_MAX_OUTPUT_TOKENS"] = "4096"

        # Call get_config
        config = get_config()

        # Verify the behavior: token count is set to specified value
        self.assertEqual(config.max_output_tokens, 4096)

    def test_gac_max_output_tokens_invalid(self):
        """Test that invalid GAC_MAX_OUTPUT_TOKENS value falls back to default."""
        # Set environment variable with invalid token count
        os.environ["GAC_MAX_OUTPUT_TOKENS"] = "not_a_number"

        # Call get_config
        config = get_config()

        # Verify the behavior: token count falls back to default
        self.assertEqual(config.max_output_tokens, DEFAULT_CONFIG["max_output_tokens"])


def test_config_wizard_provider_selection():
    """Test that the configuration wizard allows selecting a provider and entering a model."""
    # Mock user selections
    mock_select = MagicMock()
    mock_select.ask.side_effect = ["anthropic"]
    mock_text = MagicMock()
    mock_text.ask.side_effect = ["custom-model-name"]
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    # Run the wizard with mocked inputs
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        with patch("questionary.select", return_value=mock_select):
            with patch("questionary.text", return_value=mock_text):
                with patch("questionary.confirm", return_value=mock_confirm):
                    config = run_config_wizard()

                    # Verify the behavior: wizard returns valid config with selected provider and model  # noqa: E501
                    assert config is not None
                    assert config.model == "anthropic:custom-model-name"


def test_config_wizard_cancellation():
    """Test that the configuration wizard can be cancelled by the user."""
    # Mock user cancellation
    mock_select = MagicMock()
    mock_select.ask.return_value = "openai"
    mock_text = MagicMock()
    mock_text.ask.return_value = None  # Simulate user cancelling at model name input
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = False

    # Run the wizard with mocked inputs
    with patch("questionary.select", return_value=mock_select):
        with patch("questionary.text", return_value=mock_text):
            with patch("questionary.confirm", return_value=mock_confirm):
                config = run_config_wizard()

                # Verify the behavior: wizard returns None when cancelled
                assert config is None


def test_config_wizard_validation():
    """Test that wizard-generated configurations pass validation."""
    # Mock user selections
    mock_select = MagicMock()
    mock_select.ask.side_effect = ["groq"]
    mock_text = MagicMock()
    mock_text.ask.side_effect = ["custom-groq-model"]
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    # Run the wizard with mocked inputs
    with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}):
        with patch("questionary.select", return_value=mock_select):
            with patch("questionary.text", return_value=mock_text):
                with patch("questionary.confirm", return_value=mock_confirm):
                    config = run_config_wizard()

                    # Verify the behavior: generated config is valid
                    assert config is not None
                    assert config.model == "groq:custom-groq-model"
                    assert config.use_formatting is True


def test_config_wizard_formatting_option():
    """Test that the formatting option can be toggled in the wizard."""
    # Mock user selections for two different runs
    mock_select = MagicMock()
    mock_select.ask.side_effect = ["mistral", "openai"]
    mock_text = MagicMock()
    mock_text.ask.side_effect = ["mistral-large-latest", "gpt-4o"]
    mock_confirm = MagicMock()
    mock_confirm.ask.side_effect = [False, True, True, True]

    # Run the wizard twice with different formatting choices
    with patch.dict(os.environ, {"MISTRAL_API_KEY": "test_key", "OPENAI_API_KEY": "test_key"}):
        with patch("questionary.select", return_value=mock_select):
            with patch("questionary.text", return_value=mock_text):
                with patch("questionary.confirm", return_value=mock_confirm):
                    # First run with formatting disabled
                    config1 = run_config_wizard()

                    # Verify the behavior: formatting is disabled in first config
                    assert config1 is not None
                    assert config1.use_formatting is False

                    # Second run with formatting enabled
                    config2 = run_config_wizard()

                    # Verify the behavior: formatting is enabled in second config
                    assert config2 is not None
                    assert config2.use_formatting is True


def test_config_wizard_model_selection():
    """Test that the wizard allows selecting different models for each provider."""
    # Define test cases for different providers and models
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

    # Test each provider and model combination
    with patch.dict(os.environ, env_vars, clear=True):
        for provider, models in providers_and_models.items():
            for model in models:
                # Mock user selections
                mock_select = MagicMock()
                # Mock two select calls - first for provider, second for save location
                mock_select.ask.side_effect = [provider, "none"]  # none = don't save

                with (
                    patch("questionary.select", return_value=mock_select),
                    patch("questionary.text", return_value=MagicMock(ask=lambda: model)),
                    patch("questionary.confirm", return_value=MagicMock(ask=lambda: True)),
                ):
                    # Run the wizard with mocked inputs
                    config = run_config_wizard()

                    # Verify: wizard returns config with selected provider and model
                    assert config is not None
                    assert config.model == f"{provider}:{model}"


def test_config_precedence():
    """Test that configuration precedence is respected."""
    # Set up environment variables for testing
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "mock-api-key",  # Required for all tests
        },
        clear=True,
    ):

        # Test 1: Only default config (from DEFAULT_CONFIG)
        # Clear any specific config values
        for var in ["GAC_MODEL", "GAC_USE_FORMATTING"]:
            if var in os.environ:
                del os.environ[var]

        config = get_config()
        assert config.model == DEFAULT_CONFIG["model"]

        # Test 2: Environment variable overrides default
        os.environ["GAC_MODEL"] = "anthropic:env-model"
        config = get_config()
        assert config.model == "anthropic:env-model"

        # Test 3: Direct modification of Config object
        # This verifies that we can create a Config object with different values
        custom_config = Config(
            model="anthropic:custom-model",
            use_formatting=False,
            max_output_tokens=500,
            warning_limit_input_tokens=20000,
            api_key="custom-key",
        )
        assert custom_config.model == "anthropic:custom-model"
        assert custom_config.use_formatting is False
        assert custom_config.max_output_tokens == 500


if __name__ == "__main__":
    unittest.main()
