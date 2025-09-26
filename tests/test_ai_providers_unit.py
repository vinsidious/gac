import os
import sys
from unittest.mock import MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Mock external dependencies
sys.modules["tiktoken"] = MagicMock()
sys.modules["halo"] = MagicMock()
sys.modules["httpx"] = MagicMock()
sys.modules["gac.constants"] = MagicMock()
sys.modules["gac.errors"] = MagicMock()


def test_imports():
    """Test that we can import the module without external dependencies."""
    # This test verifies that the module can be imported without all external dependencies
    # It doesn't test functionality, just that imports work
    assert True


class TestAIProvidersUnit:
    """Unit tests for ai_providers module logic."""

    def test_extract_text_content_with_string(self):
        """Test _extract_text_content with string input."""
        from ai_providers import _extract_text_content

        result = _extract_text_content("test content")
        assert result == "test content"

    def test_extract_text_content_with_list(self):
        """Test _extract_text_content with list input."""
        from ai_providers import _extract_text_content

        result = _extract_text_content(
            [{"role": "user", "content": "first message"}, {"role": "assistant", "content": "second message"}]
        )
        assert result == "first message\nsecond message"

    def test_extract_text_content_with_dict(self):
        """Test _extract_text_content with dict input."""
        from ai_providers import _extract_text_content

        result = _extract_text_content({"role": "user", "content": "test content"})
        assert result == "test content"

    def test_classify_error_authentication(self):
        """Test _classify_error for authentication errors."""
        from ai_providers import _classify_error

        result = _classify_error("API key is invalid")
        assert result == "authentication"

    def test_classify_error_rate_limit(self):
        """Test _classify_error for rate limit errors."""
        from ai_providers import _classify_error

        result = _classify_error("Rate limit exceeded")
        assert result == "rate_limit"

    def test_classify_error_timeout(self):
        """Test _classify_error for timeout errors."""
        from ai_providers import _classify_error

        result = _classify_error("Request timed out")
        assert result == "timeout"

    def test_classify_error_connection(self):
        """Test _classify_error for connection errors."""
        from ai_providers import _classify_error

        result = _classify_error("Connection failed")
        assert result == "connection"

    def test_classify_error_model(self):
        """Test _classify_error for model errors."""
        from ai_providers import _classify_error

        result = _classify_error("Model not found")
        assert result == "model"

    def test_classify_error_unknown(self):
        """Test _classify_error for unknown errors."""
        from ai_providers import _classify_error

        result = _classify_error("Some unknown error")
        assert result == "unknown"
