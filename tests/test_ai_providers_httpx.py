"""Tests for ai_providers module using httpx directly."""

import os

# Add src to the path so we can import gac modules
import sys
from unittest.mock import MagicMock, patch

# Import the functions from the module for testing direct API calls
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gac.providers.anthropic import generate as anthropic_generate
from gac.providers.cerebras import generate as cerebras_generate
from gac.providers.groq import generate as groq_generate
from gac.providers.ollama import generate as ollama_generate
from gac.providers.openai import generate as openai_generate
from gac.providers.openrouter import generate as openrouter_generate


# Simple AIError class for testing purposes
class AIError(Exception):
    def __init__(self, message, error_type=None):
        super().__init__(message)
        self.error_type = error_type


class TestHttpxBasedProviders:
    """Tests for the httpx-based provider functions."""

    @patch("gac.providers.openai.httpx.Client")
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

    @patch("gac.providers.anthropic.httpx.Client")
    def test_anthropic_generate_with_httpx(self, mock_httpx_client_class):
        """Test gac.providers.anthropic.generate uses httpx directly."""
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

    @patch("gac.providers.groq.httpx.Client")
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

    @patch("gac.providers.cerebras.httpx.Client")
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

    @patch("gac.providers.ollama.httpx.Client")
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

    @patch("gac.providers.openrouter.httpx.Client")
    def test_openrouter_generate_with_httpx(self, mock_httpx_client_class):
        """Test openrouter_generate uses httpx directly and applies optional headers."""
        mock_client = MagicMock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "chore: tidy config"}}]}
        mock_client.post.return_value = mock_response

        env_vars = {
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_SITE_URL": "https://example.com",
            "OPENROUTER_SITE_NAME": "Example App",
        }

        with patch.dict(os.environ, env_vars):
            result = openrouter_generate(model="openrouter/auto", prompt="Generate", quiet=True)

        assert result == "chore: tidy config"
        call_args = mock_client.post.call_args
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert call_args.kwargs["headers"]["HTTP-Referer"] == "https://example.com"
        assert call_args.kwargs["headers"]["X-Title"] == "Example App"
        assert call_args.kwargs["json"]["model"] == "openrouter/auto"
