"""Unit tests for AI provider functionality.

These tests run without any external dependencies and test core logic.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402

import gac.ai_utils as ai_providers  # noqa: E402
from gac.errors import AIError  # noqa: E402


class TestProviderImports:
    """Test that all provider modules can be imported."""

    def test_import_providers(self):
        """Test that all provider modules can be imported."""
        from gac.providers import (  # noqa: F401
            anthropic,
            cerebras,
            groq,
            ollama,
            openai,
            openrouter,
            zai,
        )

    def test_import_provider_functions(self):
        """Test that all provider functions can be imported."""
        from gac.providers.anthropic import call_anthropic_api  # noqa: F401
        from gac.providers.cerebras import call_cerebras_api  # noqa: F401
        from gac.providers.groq import call_groq_api  # noqa: F401
        from gac.providers.ollama import call_ollama_api  # noqa: F401
        from gac.providers.openai import call_openai_api  # noqa: F401
        from gac.providers.openrouter import call_openrouter_api  # noqa: F401
        from gac.providers.zai import call_zai_api  # noqa: F401


class TestAIUtils:
    """Test AI utility functions."""

    def test_classify_error_authentication(self):
        """Test _classify_error for authentication errors."""
        result = ai_providers._classify_error("API key is invalid")
        assert result == "authentication"

    def test_classify_error_rate_limit(self):
        """Test _classify_error for rate limit errors."""
        result = ai_providers._classify_error("Rate limit exceeded")
        assert result == "rate_limit"

    def test_classify_error_timeout(self):
        """Test _classify_error for timeout errors."""
        result = ai_providers._classify_error("Request timed out")
        assert result == "timeout"

    def test_classify_error_connection(self):
        """Test _classify_error for connection errors."""
        result = ai_providers._classify_error("Connection failed")
        assert result == "connection"

    def test_classify_error_model(self):
        """Test _classify_error for model errors."""
        result = ai_providers._classify_error("Model not found")
        assert result == "model"

    def test_classify_error_unknown(self):
        """Test _classify_error for unknown errors."""
        result = ai_providers._classify_error("Some unknown error")
        assert result == "unknown"


class TestAIError:
    """Test AIError class."""

    def test_ai_error_class_exists(self):
        """Test that AIError class exists and can be instantiated."""
        error = AIError("Test error")
        assert str(error) == "Test error"

    def test_ai_error_with_type(self):
        """Test AIError with error type."""
        error = AIError("Test error", error_type="model")
        assert error.error_type == "model"


class TestZAIProvider:
    """Test ZAI provider functionality."""

    def test_zai_api_import(self):
        """Test that call_zai_api can be imported."""
        try:
            from gac.providers.zai import call_zai_api

            assert callable(call_zai_api)
        except ImportError:
            self.fail("Could not import call_zai_api")

    def test_zai_api_missing_key(self):
        """Test that zai provider raises error when API key is missing."""
        # Mock environment to not have the API key
        if "ZAI_API_KEY" in os.environ:
            del os.environ["ZAI_API_KEY"]

        from gac.errors import AIError
        from gac.providers.zai import call_zai_api

        with pytest.raises(AIError) as exc_info:
            call_zai_api("model", [], 0.7, 1000)

        assert "ZAI_API_KEY not found in environment variables" in str(exc_info.value)

    def test_zai_coding_api_import(self):
        """Test that call_zai_coding_api can be imported."""
        try:
            from gac.providers.zai import call_zai_coding_api

            assert callable(call_zai_coding_api)
        except ImportError:
            self.fail("Could not import call_zai_coding_api")

    def test_zai_coding_api_missing_key(self):
        """Test that zai-coding provider raises error when API key is missing."""
        # Mock environment to not have the API key
        if "ZAI_API_KEY" in os.environ:
            del os.environ["ZAI_API_KEY"]

        from gac.errors import AIError
        from gac.providers.zai import call_zai_coding_api

        with pytest.raises(AIError) as exc_info:
            call_zai_coding_api("model", [], 0.7, 1000)

        assert "ZAI_API_KEY not found in environment variables" in str(exc_info.value)
