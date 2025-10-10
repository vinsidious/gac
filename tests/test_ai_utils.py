"""Unit tests for AI utility functions.

These tests run without any external dependencies and test core logic.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gac.ai_utils as ai_utils  # noqa: E402
from gac.errors import AIError  # noqa: E402


class TestClassifyError:
    """Test _classify_error function."""

    def test_classify_error_authentication(self):
        """Test _classify_error for authentication errors."""
        assert ai_utils._classify_error("Invalid API key") == "authentication"
        assert ai_utils._classify_error("Unauthorized access") == "authentication"
        assert ai_utils._classify_error("Authentication failed") == "authentication"
        assert ai_utils._classify_error("API key is invalid") == "authentication"

    def test_classify_error_rate_limit(self):
        """Test _classify_error for rate limit errors."""
        assert ai_utils._classify_error("Rate limit exceeded") == "rate_limit"
        assert ai_utils._classify_error("Too many requests") == "rate_limit"

    def test_classify_error_timeout(self):
        """Test _classify_error for timeout errors."""
        assert ai_utils._classify_error("Request timed out") == "timeout"
        assert ai_utils._classify_error("Request timeout") == "timeout"
        assert ai_utils._classify_error("Connection timed out") == "timeout"

    def test_classify_error_connection(self):
        """Test _classify_error for connection errors."""
        assert ai_utils._classify_error("Connection failed") == "connection"
        assert ai_utils._classify_error("Network connection failed") == "connection"
        assert ai_utils._classify_error("Connection error") == "connection"

    def test_classify_error_model(self):
        """Test _classify_error for model errors."""
        assert ai_utils._classify_error("Model not found") == "model"
        assert ai_utils._classify_error("Invalid model") == "model"

    def test_classify_error_unknown(self):
        """Test _classify_error for unknown errors."""
        assert ai_utils._classify_error("Some unknown error") == "unknown"
        assert ai_utils._classify_error("Random error") == "unknown"
        assert ai_utils._classify_error("Some other issue") == "unknown"


class TestCountTokens:
    """Test count_tokens function."""

    def test_count_tokens(self):
        """Test token counting functionality."""
        # Test with string content
        text = "Hello, world!"
        token_count = ai_utils.count_tokens(text, "openai:gpt-4")
        assert token_count > 0
        assert isinstance(token_count, int)

    def test_count_tokens_empty_content(self):
        """Test token counting with empty content."""
        assert ai_utils.count_tokens("", "openai:gpt-4") == 0
        assert ai_utils.count_tokens([], "openai:gpt-4") == 0
        assert ai_utils.count_tokens({}, "openai:gpt-4") == 0


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
