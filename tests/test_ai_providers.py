"""Tests for ai_providers module."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.ai_providers import (
    _classify_error,
    anthropic_generate,
    cerebras_generate,
    count_tokens,
    groq_generate,
    ollama_generate,
    openai_generate,
)
from gac.errors import AIError


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


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
class TestOpenaiGenerate:
    """Tests for the openai_generate function."""

    @patch("gac.ai_providers.openai.OpenAI")
    def test_openai_generate_string_prompt(self, mock_openai_class):
        """Test openai_generate with string prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="feat: Add new feature"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with string prompt
        result = openai_generate(model="gpt-4", prompt="Generate a commit message", quiet=True)

        assert result == "feat: Add new feature"

    @patch("gac.ai_providers.openai.OpenAI")
    def test_openai_generate_tuple_prompt(self, mock_openai_class):
        """Test openai_generate with tuple prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="fix: Resolve bug"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with tuple prompt
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a commit message for a bug fix."
        result = openai_generate(
            model="gpt-4", prompt=(system_prompt, user_prompt), temperature=0.5, max_tokens=100, quiet=True
        )

        assert result == "fix: Resolve bug"

    @patch("gac.ai_providers.openai.OpenAI")
    @patch("gac.ai_providers.Halo")
    def test_openai_generate_with_spinner(self, mock_halo_class, mock_openai_class):
        """Test openai_generate with spinner."""
        # Setup mocks
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="docs: Update README"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with spinner enabled
        result = openai_generate(model="gpt-4", prompt="test", quiet=False)

        assert result == "docs: Update README"

        # Verify spinner was used
        mock_halo_class.assert_called_once()
        mock_spinner.start.assert_called_once()
        mock_spinner.succeed.assert_called_once_with("Generated commit message with OpenAI gpt-4")

    @patch("gac.ai_providers.openai.OpenAI")
    @patch("gac.ai_providers.time.sleep")
    def test_openai_generate_retry_logic(self, mock_sleep, mock_openai_class):
        """Test retry logic when generation fails."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # First two attempts fail, third succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="feat: Success after retries"))]
        mock_client.chat.completions.create.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_response,
        ]

        # Test with retries
        result = openai_generate(model="gpt-4", prompt="test", max_retries=3, quiet=True)

        assert result == "feat: Success after retries"
        assert mock_client.chat.completions.create.call_count == 3

        # Verify sleep was called for retries
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2)
        mock_sleep.assert_any_call(4)

    @patch("gac.ai_providers.openai.OpenAI")
    @patch("gac.ai_providers.time.sleep")
    def test_openai_generate_max_retries_exceeded(self, mock_sleep, mock_openai_class):
        """Test that AIError is raised when max retries are exceeded."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # All attempts fail
        mock_client.chat.completions.create.side_effect = Exception("Persistent error")

        # Test max retries exceeded
        with pytest.raises(AIError) as exc_info:
            openai_generate(model="gpt-4", prompt="test", max_retries=2, quiet=True)

        assert "Failed to generate commit message after 2 attempts" in str(exc_info.value)

    def test_openai_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                openai_generate(model="gpt-4", prompt="test", quiet=True)
            assert "OPENAI_API_KEY environment variable not set" in str(exc_info.value)
            assert exc_info.value.error_type == "model"


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
class TestAnthropicGenerate:
    """Tests for the anthropic_generate function."""

    @patch("gac.ai_providers.anthropic.Anthropic")
    def test_anthropic_generate_string_prompt(self, mock_anthropic_class):
        """Test anthropic_generate with string prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="feat: Add new feature")]
        mock_client.messages.create.return_value = mock_response

        # Test with string prompt
        result = anthropic_generate(model="claude-3-haiku", prompt="Generate a commit message", quiet=True)

        assert result == "feat: Add new feature"

        # Verify the message format
        call_args = mock_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Generate a commit message"

    @patch("gac.ai_providers.anthropic.Anthropic")
    def test_anthropic_generate_tuple_prompt(self, mock_anthropic_class):
        """Test anthropic_generate with tuple prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="fix: Resolve bug")]
        mock_client.messages.create.return_value = mock_response

        # Test with tuple prompt
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a commit message for a bug fix."
        result = anthropic_generate(
            model="claude-3-opus", prompt=(system_prompt, user_prompt), temperature=0.5, max_tokens=100, quiet=True
        )

        assert result == "fix: Resolve bug"

        # Verify the message format
        call_args = mock_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == user_prompt

        # Verify system prompt was passed
        assert call_args.kwargs["system"] == system_prompt

    @patch("gac.ai_providers.anthropic.Anthropic")
    @patch("gac.ai_providers.Halo")
    def test_anthropic_generate_with_spinner(self, mock_halo_class, mock_anthropic_class):
        """Test anthropic_generate with spinner."""
        # Setup mocks
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="docs: Update README")]
        mock_client.messages.create.return_value = mock_response

        # Test with spinner enabled
        result = anthropic_generate(model="claude-3-haiku", prompt="test", quiet=False)

        assert result == "docs: Update README"

        # Verify spinner was used
        mock_halo_class.assert_called_once()
        mock_spinner.start.assert_called_once()
        mock_spinner.succeed.assert_called_once_with("Generated commit message with Anthropic claude-3-haiku")

    @patch("gac.ai_providers.anthropic.Anthropic")
    @patch("gac.ai_providers.time.sleep")
    def test_anthropic_generate_retry_logic(self, mock_sleep, mock_anthropic_class):
        """Test retry logic when generation fails."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # First two attempts fail, third succeeds
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="feat: Success after retries")]
        mock_client.messages.create.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_response,
        ]

        # Test with retries
        result = anthropic_generate(model="claude-3-haiku", prompt="test", max_retries=3, quiet=True)

        assert result == "feat: Success after retries"
        assert mock_client.messages.create.call_count == 3

    def test_anthropic_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                anthropic_generate(model="claude-3-haiku", prompt="test", quiet=True)
            assert "ANTHROPIC_API_KEY environment variable not set" in str(exc_info.value)
            assert exc_info.value.error_type == "model"


@patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"})
class TestCerebrasGenerate:
    """Tests for the cerebras_generate function."""

    @patch("gac.ai_providers.cerebras.Client")
    def test_cerebras_generate_string_prompt(self, mock_cerebras_class):
        """Test cerebras_generate with string prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_cerebras_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="feat: Add new feature"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with string prompt
        result = cerebras_generate(model="llama3.1-8b", prompt="Generate a commit message", quiet=True)

        assert result == "feat: Add new feature"

    @patch("gac.ai_providers.cerebras.Client")
    def test_cerebras_generate_tuple_prompt(self, mock_cerebras_class):
        """Test cerebras_generate with tuple prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_cerebras_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="fix: Resolve bug"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with tuple prompt
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a commit message for a bug fix."
        result = cerebras_generate(
            model="llama3.1-70b", prompt=(system_prompt, user_prompt), temperature=0.5, max_tokens=100, quiet=True
        )

        assert result == "fix: Resolve bug"

        # Verify the request was made with correct data
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "llama3.1-70b"
        assert call_args.kwargs["temperature"] == 0.5
        assert call_args.kwargs["max_tokens"] == 100

    @patch("gac.ai_providers.cerebras.Client")
    def test_cerebras_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                cerebras_generate(model="llama3.1-8b", prompt="test", quiet=True)
            assert "CEREBRAS_API_KEY environment variable not set" in str(exc_info.value)
            assert exc_info.value.error_type == "model"

    @patch("gac.ai_providers.cerebras.Client")
    def test_cerebras_generate_library_not_installed(self, mock_cerebras_class):
        """Test that AIError is raised when cerebras library is not installed."""
        # Mock the cerebras library to be None
        with patch("gac.ai_providers.cerebras", None):
            with pytest.raises(AIError) as exc_info:
                cerebras_generate(model="llama3.1-8b", prompt="test", quiet=True)
            assert "Cerebras library not installed" in str(exc_info.value)
            assert exc_info.value.error_type == "model"


@patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
class TestGroqGenerate:
    """Tests for the groq_generate function."""

    @patch("gac.ai_providers.groq.Groq")
    def test_groq_generate_string_prompt(self, mock_groq_class):
        """Test groq_generate with string prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="feat: Add new feature"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with string prompt
        result = groq_generate(model="llama3-8b-8192", prompt="Generate a commit message", quiet=True)

        assert result == "feat: Add new feature"

    @patch("gac.ai_providers.groq.Groq")
    def test_groq_generate_tuple_prompt(self, mock_groq_class):
        """Test groq_generate with tuple prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="fix: Resolve bug"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with tuple prompt
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a commit message for a bug fix."
        result = groq_generate(
            model="llama3-70b-8192", prompt=(system_prompt, user_prompt), temperature=0.5, max_tokens=100, quiet=True
        )

        assert result == "fix: Resolve bug"

    @patch("gac.ai_providers.groq.Groq")
    @patch("gac.ai_providers.Halo")
    def test_groq_generate_with_spinner(self, mock_halo_class, mock_groq_class):
        """Test groq_generate with spinner."""
        # Setup mocks
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="docs: Update README"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test with spinner enabled
        result = groq_generate(model="llama3-8b-8192", prompt="test", quiet=False)

        assert result == "docs: Update README"

        # Verify spinner was used
        mock_halo_class.assert_called_once()
        mock_spinner.start.assert_called_once()
        mock_spinner.succeed.assert_called_once_with("Generated commit message with Groq llama3-8b-8192")

    @patch("gac.ai_providers.groq.Groq")
    @patch("gac.ai_providers.time.sleep")
    def test_groq_generate_retry_logic(self, mock_sleep, mock_groq_class):
        """Test retry logic when generation fails."""
        # Setup mock
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        # First two attempts fail, third succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="feat: Success after retries"))]
        mock_client.chat.completions.create.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_response,
        ]

        # Test with retries
        result = groq_generate(model="llama3-8b-8192", prompt="test", max_retries=3, quiet=True)

        assert result == "feat: Success after retries"
        assert mock_client.chat.completions.create.call_count == 3

        # Verify sleep was called for retries
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2)
        mock_sleep.assert_any_call(4)

    def test_groq_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                groq_generate(model="llama3-8b-8192", prompt="test", quiet=True)
            assert "GROQ_API_KEY environment variable not set" in str(exc_info.value)
            assert exc_info.value.error_type == "model"


class TestOllamaGenerate:
    """Tests for the ollama_generate function."""

    @patch("gac.ai_providers.httpx.Client")
    def test_ollama_generate_string_prompt(self, mock_httpx_client_class):
        """Test ollama_generate with string prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "feat: Add new feature"}}
        mock_client.post.return_value = mock_response

        # Test with string prompt
        result = ollama_generate(model="llama3", prompt="Generate a commit message", quiet=True)

        assert result == "feat: Add new feature"

    @patch("gac.ai_providers.httpx.Client")
    def test_ollama_generate_tuple_prompt(self, mock_httpx_client_class):
        """Test ollama_generate with tuple prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "fix: Resolve bug"}}
        mock_client.post.return_value = mock_response

        # Test with tuple prompt
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a commit message for a bug fix."
        result = ollama_generate(
            model="mistral", prompt=(system_prompt, user_prompt), temperature=0.5, max_tokens=100, quiet=True
        )

        assert result == "fix: Resolve bug"

        # Verify the request was made with correct data
        call_args = mock_client.post.call_args
        json_data = call_args.kwargs["json"]
        assert json_data["model"] == "mistral"
        assert json_data["stream"] is False
        assert json_data["options"]["temperature"] == 0.5
        assert json_data["options"]["num_predict"] == 100

    @patch("gac.ai_providers.httpx.Client")
    def test_ollama_generate_api_error(self, mock_httpx_client_class):
        """Test ollama_generate handles API errors correctly."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_client.post.return_value = mock_response

        # Test API error
        with pytest.raises(AIError) as exc_info:
            ollama_generate(model="nonexistent-model", prompt="test", quiet=True)

        assert "Ollama API returned status code 404" in str(exc_info.value)
        assert exc_info.value.error_type == "model"

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.Halo")
    def test_ollama_generate_with_spinner(self, mock_halo_class, mock_httpx_client_class):
        """Test ollama_generate with spinner."""
        # Setup mocks
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "docs: Update README"}}
        mock_client.post.return_value = mock_response

        # Test with spinner enabled
        result = ollama_generate(model="llama3", prompt="test", quiet=False)

        assert result == "docs: Update README"

        # Verify spinner was used
        mock_halo_class.assert_called_once()
        mock_spinner.start.assert_called_once()
        mock_spinner.succeed.assert_called_once_with("Generated commit message with Ollama llama3")

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.time.sleep")
    def test_ollama_generate_retry_logic(self, mock_sleep, mock_httpx_client_class):
        """Test retry logic when generation fails."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        # First two attempts fail, third succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "feat: Success after retries"}}
        mock_client.post.side_effect = [
            MagicMock(status_code=500, text="Server error"),
            MagicMock(status_code=500, text="Server error"),
            mock_response,
        ]

        # Test with retries
        result = ollama_generate(model="llama3", prompt="test", max_retries=3, quiet=True)

        assert result == "feat: Success after retries"
        assert mock_client.post.call_count == 3

        # Verify sleep was called for retries
        assert mock_sleep.call_count == 2

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.time.sleep")
    def test_ollama_generate_max_retries_exceeded(self, mock_sleep, mock_httpx_client_class):
        """Test that AIError is raised when max retries are exceeded."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        # All attempts fail
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_client.post.return_value = mock_response

        # Test max retries exceeded
        with pytest.raises(AIError) as exc_info:
            ollama_generate(model="llama3", prompt="test", max_retries=2, quiet=True)

        assert "Failed to generate commit message after 2 attempts" in str(exc_info.value)

    @patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://custom-host:8000"})
    @patch("gac.ai_providers.httpx.Client")
    def test_ollama_generate_custom_base_url(self, mock_httpx_client_class):
        """Test ollama_generate uses custom base URL from environment."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "feat: Custom base URL"}}
        mock_client.post.return_value = mock_response

        # Test with custom base URL
        result = ollama_generate(model="llama3", prompt="test", quiet=True)

        assert result == "feat: Custom base URL"

        # Verify the client was created with the custom base URL
        mock_httpx_client_class.assert_called_once_with(base_url="http://custom-host:8000", timeout=30.0)
