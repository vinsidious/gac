"""Tests for ai_providers module."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.ai_utils import _classify_error, count_tokens
from gac.errors import AIError
from gac.providers.anthropic import call_anthropic_api
from gac.providers.cerebras import call_cerebras_api
from gac.providers.groq import call_groq_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api


class TestAiProvidersUtils:
    """Tests for the AI providers utilities."""

    def test_classify_error_authentication(self):
        """Test error classification for authentication errors."""
        assert _classify_error("Invalid API key") == "authentication"
        assert _classify_error("Unauthorized access") == "authentication"
        assert _classify_error("Authentication failed") == "authentication"

    def test_classify_error_timeout(self):
        """Test error classification for timeout errors."""
        assert _classify_error("Request timeout") == "timeout"
        assert _classify_error("Connection timed out") == "timeout"

    def test_classify_error_rate_limit(self):
        """Test error classification for rate limit errors."""
        assert _classify_error("Rate limit exceeded") == "rate_limit"
        assert _classify_error("Too many requests") == "rate_limit"

    def test_classify_error_connection(self):
        """Test error classification for connection errors."""
        assert _classify_error("Network connection failed") == "connection"
        assert _classify_error("Connection error") == "connection"

    def test_classify_error_model(self):
        """Test error classification for model errors."""
        assert _classify_error("Model not found") == "model"
        assert _classify_error("Invalid model") == "model"

    def test_classify_error_unknown(self):
        """Test error classification for unknown errors."""
        assert _classify_error("Random error") == "unknown"
        assert _classify_error("Some other issue") == "unknown"

    def test_count_tokens(self):
        """Test token counting functionality."""
        # Test with string content
        text = "Hello, world!"
        token_count = count_tokens(text, "openai:gpt-4")
        assert token_count > 0
        assert isinstance(token_count, int)

    def test_count_tokens_empty_content(self):
        """Test token counting with empty content."""
        assert count_tokens("", "openai:gpt-4") == 0
        assert count_tokens([], "openai:gpt-4") == 0
        assert count_tokens({}, "openai:gpt-4") == 0


class TestAPIKeyValidation:
    """Tests for API key validation in each provider."""

    def test_openai_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_openai_api(
                    model="gpt-4", messages=[{"role": "user", "content": "test"}], temperature=0.7, max_tokens=100
                )
            assert "OPENAI_API_KEY not found in environment variables" in str(exc_info.value)

    def test_anthropic_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_anthropic_api(
                    model="claude-3-haiku",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "ANTHROPIC_API_KEY not found in environment variables" in str(exc_info.value)

    def test_cerebras_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_cerebras_api(
                    model="llama3.1-8b", messages=[{"role": "user", "content": "test"}], temperature=0.7, max_tokens=100
                )
            assert "CEREBRAS_API_KEY not found in environment variables" in str(exc_info.value)

    def test_groq_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_groq_api(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "GROQ_API_KEY not found in environment variables" in str(exc_info.value)

    def test_openrouter_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_openrouter_api(
                    model="openrouter/auto",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "OPENROUTER_API_KEY environment variable not set" in str(exc_info.value)
