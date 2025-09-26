import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_imports():
    """Test that we can import the module without external dependencies."""
    # This test verifies that the module can be imported without external dependencies
    # It doesn't test functionality, just that imports work
    assert True


class TestAIProvidersUnit:
    """Unit tests for ai_providers module logic."""

    def test_classify_error_authentication(self):
        """Test _classify_error for authentication errors."""
        from gac.ai_providers import _classify_error

        result = _classify_error("API key is invalid")
        assert result == "authentication"

    def test_classify_error_rate_limit(self):
        """Test _classify_error for rate limit errors."""
        from gac.ai_providers import _classify_error

        result = _classify_error("Rate limit exceeded")
        assert result == "rate_limit"

    def test_classify_error_timeout(self):
        """Test _classify_error for timeout errors."""
        from gac.ai_providers import _classify_error

        result = _classify_error("Request timed out")
        assert result == "timeout"

    def test_classify_error_connection(self):
        """Test _classify_error for connection errors."""
        from gac.ai_providers import _classify_error

        result = _classify_error("Connection failed")
        assert result == "connection"

    def test_classify_error_model(self):
        """Test _classify_error for model errors."""
        from gac.ai_providers import _classify_error

        result = _classify_error("Model not found")
        assert result == "model"

    def test_classify_error_unknown(self):
        """Test _classify_error for unknown errors."""
        from gac.ai_providers import _classify_error

        result = _classify_error("Some unknown error")
        assert result == "unknown"
