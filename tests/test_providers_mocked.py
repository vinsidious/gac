"""Mocked tests for AI provider HTTP interactions.

These tests use mocked HTTP calls to test provider behavior without making real API calls.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src to the path so we can import gac modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.providers.anthropic import call_anthropic_api  # noqa: E402
from gac.providers.cerebras import call_cerebras_api  # noqa: E402
from gac.providers.groq import call_groq_api  # noqa: E402
from gac.providers.ollama import call_ollama_api  # noqa: E402
from gac.providers.openai import call_openai_api  # noqa: E402
from gac.providers.openrouter import call_openrouter_api  # noqa: E402
from gac.providers.zai import call_zai_api  # noqa: E402


class TestProviderHttpxCalls:
    """Test that all provider functions use httpx correctly."""

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
            mock_post.assert_called_once()

    @patch("gac.providers.anthropic.httpx.post")
    def test_anthropic_generate_with_httpx(self, mock_post):
        """Test call_anthropic_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": [{"text": "feat: Add new feature"}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_anthropic_api(model="claude-3", messages=messages, temperature=0.7, max_tokens=100)

            assert result == "feat: Add new feature"
            mock_post.assert_called_once()

    @patch("gac.providers.groq.httpx.post")
    def test_groq_generate_with_httpx(self, mock_post):
        """Test call_groq_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "feat: Add new feature"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_groq_api(model="llama-3.1-70b", messages=messages, temperature=0.7, max_tokens=100)

            assert result == "feat: Add new feature"
            mock_post.assert_called_once()

    @patch("gac.providers.cerebras.httpx.post")
    def test_cerebras_generate_with_httpx(self, mock_post):
        """Test call_cerebras_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "feat: Add new feature"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_cerebras_api(model="llama3.1-8b", messages=messages, temperature=0.7, max_tokens=100)

            assert result == "feat: Add new feature"
            mock_post.assert_called_once()

    @patch("gac.providers.ollama.httpx.post")
    def test_ollama_generate_with_httpx(self, mock_post):
        """Test call_ollama_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "feat: Add new feature"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Generate a commit message"}]
        result = call_ollama_api(model="llama2", messages=messages, temperature=0.7, max_tokens=100)

        assert result == "feat: Add new feature"
        mock_post.assert_called_once()

    @patch("gac.providers.openrouter.httpx.post")
    def test_openrouter_generate_with_httpx(self, mock_post):
        """Test call_openrouter_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "feat: Add new feature"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_openrouter_api(
                model="mistralai/mistral-7b-instruct", messages=messages, temperature=0.7, max_tokens=100
            )

            assert result == "feat: Add new feature"
            mock_post.assert_called_once()

    @patch("gac.providers.zai.httpx.post")
    def test_zai_generate_with_httpx(self, mock_post):
        """Test call_zai_api uses httpx directly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "feat: Add new feature"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            messages = [{"role": "user", "content": "Generate a commit message"}]
            result = call_zai_api(model="glm-4.5-air", messages=messages, temperature=0.7, max_tokens=100)

            assert result == "feat: Add new feature"
            mock_post.assert_called_once()

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
