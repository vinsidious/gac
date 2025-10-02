"""Tests for ai_providers module using httpx directly."""

import os

# Add src to the path so we can import gac modules
import sys
from unittest.mock import MagicMock, patch

# Import the functions from the module for testing direct API calls
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gac.providers.anthropic import call_anthropic_api
from gac.providers.cerebras import call_cerebras_api
from gac.providers.groq import call_groq_api
from gac.providers.ollama import call_ollama_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api
from gac.providers.zai import call_zai_api


# Simple AIError class for testing purposes
class AIError(Exception):
    def __init__(self, message, error_type=None):
        super().__init__(message)
        self.error_type = error_type


class TestHttpxBasedProviders:
    """Tests for the httpx-based provider functions."""

    @patch("gac.providers.openai.httpx.post")
    def test_openai_generate_with_httpx(self, mock_post):
        """Test call_openai_api uses httpx directly."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "feat: Add new feature"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_openai_api(model="gpt-4", messages=messages, temperature=0.7, max_tokens=100)
            assert result == "feat: Add new feature"

    @patch("gac.providers.anthropic.httpx.post")
    def test_anthropic_generate_with_httpx(self, mock_post):
        """Test call_anthropic_api uses httpx directly."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": [{"text": "fix: Resolve bug"}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_anthropic_api(model="claude-3-haiku", messages=messages, temperature=0.7, max_tokens=100)
            assert result == "fix: Resolve bug"

    @patch("gac.providers.groq.httpx.post")
    def test_groq_generate_with_httpx(self, mock_post):
        """Test call_groq_api uses httpx directly."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "docs: Update README"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_groq_api(model="llama3-8b-8192", messages=messages, temperature=0.7, max_tokens=100)
            assert result == "docs: Update README"

    @patch("gac.providers.cerebras.httpx.post")
    def test_cerebras_generate_with_httpx(self, mock_post):
        """Test call_cerebras_api uses httpx directly."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "refactor: Improve code structure"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_cerebras_api(model="llama3.1-8b", messages=messages, temperature=0.7, max_tokens=100)
            assert result == "refactor: Improve code structure"

    @patch("gac.providers.ollama.httpx.post")
    def test_ollama_generate_with_httpx(self, mock_post):
        """Test call_ollama_api uses httpx directly."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test: Add unit tests"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Mock environment variable (OLLAMA_BASE_URL has a default)
        with patch.dict(os.environ, {}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_ollama_api(model="llama3", messages=messages, temperature=0.7, max_tokens=100)
            assert result == "test: Add unit tests"

    @patch("gac.providers.openrouter.httpx.post")
    def test_openrouter_generate_with_httpx(self, mock_post):
        """Test call_openrouter_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "chore: tidy config"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        env_vars = {
            "OPENROUTER_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env_vars):
            messages = [{"role": "user", "content": "Generate"}]
            result = call_openrouter_api(model="openrouter/auto", messages=messages, temperature=0.7, max_tokens=100)

        assert result == "chore: tidy config"
        call_args = mock_post.call_args
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert call_args.kwargs["json"]["model"] == "openrouter/auto"

    @patch("gac.providers.zai.httpx.post")
    def test_zai_generate_with_httpx_empty_content(self, mock_post):
        """Test call_zai_api handles empty content response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            try:
                call_zai_api(model="glm-4.5-air", messages=messages, temperature=0.7, max_tokens=100)
                raise AssertionError("Should have raised an AIError")
            except Exception as e:
                assert "empty content" in str(e)

    @patch("gac.providers.zai.httpx.post")
    def test_zai_generate_with_httpx(self, mock_post):
        """Test call_zai_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "style: Format code"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_zai_api(model="glm-4.5-air", messages=messages, temperature=0.7, max_tokens=100)
            assert result == "style: Format code"
