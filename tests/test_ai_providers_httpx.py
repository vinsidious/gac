"""Tests for ai_providers module using httpx directly."""

import os

# Add src to the path so we can import gac modules
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import the functions from the module for testing direct API calls
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "gac"))
from ai_providers import (
    anthropic_generate,
    cerebras_generate,
    groq_generate,
    ollama_generate,
    openai_generate,
)


# Simple AIError class for testing purposes
class AIError(Exception):
    def __init__(self, message, error_type=None):
        super().__init__(message)
        self.error_type = error_type


class TestHttpxBasedProviders:
    """Tests for the httpx-based provider functions."""

    @patch("gac.ai_providers.httpx.Client")
    def test_openai_generate_with_httpx(self, mock_httpx_client_class):
        """Test openai_generate uses httpx directly."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "feat: Add new feature"}}]}
        mock_client.post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            result = openai_generate(model="gpt-4", prompt="Generate a commit message", quiet=True)
            assert result == "feat: Add new feature"

    @patch("gac.ai_providers.httpx.Client")
    def test_anthropic_generate_with_httpx(self, mock_httpx_client_class):
        """Test anthropic_generate uses httpx directly."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": [{"text": "fix: Resolve bug"}]}
        mock_client.post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = anthropic_generate(model="claude-3-haiku", prompt="Generate a commit message", quiet=True)
            assert result == "fix: Resolve bug"

    @patch("gac.ai_providers.httpx.Client")
    def test_groq_generate_with_httpx(self, mock_httpx_client_class):
        """Test groq_generate uses httpx directly."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "docs: Update README"}}]}
        mock_client.post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            result = groq_generate(model="llama3-8b-8192", prompt="Generate a commit message", quiet=True)
            assert result == "docs: Update README"

    @patch("gac.ai_providers.httpx.Client")
    def test_cerebras_generate_with_httpx(self, mock_httpx_client_class):
        """Test cerebras_generate uses httpx directly."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "refactor: Improve code structure"}}]}
        mock_client.post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
            result = cerebras_generate(model="llama3.1-8b", prompt="Generate a commit message", quiet=True)
            assert result == "refactor: Improve code structure"

    @patch("gac.ai_providers.httpx.Client")
    def test_ollama_generate_with_httpx(self, mock_httpx_client_class):
        """Test ollama_generate uses httpx directly."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test: Add unit tests"}}
        mock_client.post.return_value = mock_response

        # Mock environment variable (OLLAMA_BASE_URL has a default)
        with patch.dict(os.environ, {}):
            result = ollama_generate(model="llama3", prompt="Generate a commit message", quiet=True)
            assert result == "test: Add unit tests"
