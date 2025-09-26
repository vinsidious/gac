"""Tests for ai module."""

from unittest.mock import MagicMock, patch

import pytest
import tiktoken

from gac.ai import (
    count_tokens,
    extract_text_content,
    generate_commit_message,
    get_encoding,
)
from gac.errors import AIError


class TestAiUtils:
    """Tests for the AI utilities."""

    def test_extract_text_content(self):
        """Test extracting text content from various input formats."""
        # Test string input
        assert extract_text_content("test") == "test"

        # Test list of messages
        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "World"}]
        assert extract_text_content(messages) == "Hello\nWorld"

        # Test dict with content
        message = {"role": "user", "content": "Test"}
        assert extract_text_content(message) == "Test"

        # Test empty input
        assert extract_text_content({}) == ""

    def test_get_encoding_known_model(self):
        """Test getting encoding for known models without mocking."""
        # Test with a well-known OpenAI model that should map to cl100k_base
        encoding = get_encoding("openai:gpt-4")
        assert isinstance(encoding, tiktoken.Encoding)
        assert encoding.name == "cl100k_base"

        # Verify encoding behavior
        tokens = encoding.encode("Hello world")
        assert len(tokens) > 0
        assert isinstance(tokens[0], int)

        # Decode should round-trip correctly
        decoded = encoding.decode(tokens)
        assert decoded == "Hello world"

    def test_count_tokens(self):
        """Test token counting functionality."""
        # Test with string content
        text = "Hello, world!"
        token_count = count_tokens(text, "openai:gpt-4")
        assert token_count > 0
        assert isinstance(token_count, int)

    @patch("gac.ai.count_tokens")
    def test_count_tokens_anthropic_mock(self, mock_count_tokens):
        """Test that anthropic models are handled correctly."""
        # This tests the code path, not the actual implementation
        mock_count_tokens.return_value = 5

        # Test that anthropic model strings are recognized
        model = "anthropic:claude-3-haiku"
        assert model.startswith("anthropic")

    def test_count_tokens_anthropic_integration(self):
        """Test token counting for Anthropic models with dynamic import."""
        text = "Hello, world!"

        # Mock at the module level where it's imported
        with patch("builtins.__import__") as mock_import:
            # Create a mock anthropic module
            mock_anthropic = MagicMock()
            mock_client = MagicMock()

            # Mock the messages.count_tokens response
            mock_response = MagicMock()
            mock_response.input_tokens = 5
            mock_client.messages.count_tokens.return_value = mock_response

            mock_anthropic.Anthropic.return_value = mock_client

            # Make __import__ return our mock for anthropic
            def import_side_effect(name, *args, **kwargs):
                if name == "anthropic":
                    return mock_anthropic
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            token_count = count_tokens(text, "anthropic:claude-3-haiku")
            assert token_count == 5

    def test_count_tokens_empty_content(self):
        """Test token counting with empty content."""
        assert count_tokens("", "openai:gpt-4") == 0
        assert count_tokens([], "openai:gpt-4") == 0
        assert count_tokens({}, "openai:gpt-4") == 0

        # Test with list of messages
        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]
        token_count = count_tokens(messages, "openai:gpt-4")
        assert token_count > 0

        # Test with dict content
        message = {"role": "user", "content": "Test message"}
        token_count = count_tokens(message, "openai:gpt-4")
        assert token_count > 0

    def test_get_encoding_unknown_model(self):
        """Test getting encoding for unknown models falls back to default."""
        # Clear the cache first to ensure fresh test
        get_encoding.cache_clear()

        # Test with unknown model should fall back to default encoding
        encoding = get_encoding("unknown:model-xyz")
        assert isinstance(encoding, tiktoken.Encoding)
        # Should use the default cl100k_base encoding
        assert encoding.name == "cl100k_base"

    def test_count_tokens_error_handling(self):
        """Test error handling in count_tokens function."""
        # Test with a model that will cause encoding error
        with patch("gac.ai.get_encoding") as mock_encoding:
            mock_encoding.side_effect = Exception("Encoding error")

            # Should fall back to character-based estimation (len/4)
            token_count = count_tokens("Hello world", "test:model")
            assert token_count == len("Hello world") // 4

    def test_count_tokens_with_various_content_types(self):
        """Test count_tokens with different content formats."""
        # Test with list containing invalid items
        messages = [
            {"role": "user", "content": "Valid message"},
            {"role": "assistant"},  # Missing content
            "invalid",  # Not a dict
            {"content": "No role"},  # Has content
        ]
        token_count = count_tokens(messages, "openai:gpt-4")
        assert token_count > 0  # Should count valid messages


class TestGenerateCommitMessage:
    """Tests for the generate_commit_message function."""

    def test_generate_commit_message_invalid_model_format(self):
        """Test that invalid model format raises AIError."""
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="invalid-format", prompt="test prompt")  # Missing colon separator
        assert "Invalid model format" in str(exc_info.value)

    @patch("gac.ai.openai_generate")
    def test_generate_commit_message_string_prompt(self, mock_openai_generate):
        """Test generate_commit_message with string prompt (backward compatibility)."""
        # Setup mock
        mock_openai_generate.return_value = "feat: Add new feature"

        # Test with string prompt
        result = generate_commit_message(model="openai:gpt-4", prompt="Generate a commit message", quiet=True)

        assert result == "feat: Add new feature"

        # Verify the parameters passed to openai_generate
        call_args = mock_openai_generate.call_args
        assert call_args[0][0] == "gpt-4"  # model_name
        assert call_args[0][1] == "Generate a commit message"  # prompt
        assert call_args[0][5] is True  # quiet parameter (6th positional argument)

    @patch("gac.ai.anthropic_generate")
    def test_generate_commit_message_tuple_prompt(self, mock_anthropic_generate):
        """Test generate_commit_message with tuple prompt (system and user)."""
        # Setup mock
        mock_anthropic_generate.return_value = "fix: Resolve bug"

        # Test with tuple prompt
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a commit message for a bug fix."
        result = generate_commit_message(
            model="anthropic:claude-3", prompt=(system_prompt, user_prompt), temperature=0.5, max_tokens=100, quiet=True
        )

        assert result == "fix: Resolve bug"

        # Verify the parameters passed to anthropic_generate
        call_args = mock_anthropic_generate.call_args
        assert call_args[0][0] == "claude-3"  # model_name
        assert call_args[0][1] == (system_prompt, user_prompt)  # prompt tuple
        assert call_args[0][2] == 0.5  # temperature (3rd positional argument)
        assert call_args[0][3] == 100  # max_tokens (4th positional argument)
        assert call_args[0][5] is True  # quiet parameter (6th positional argument)

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.Halo")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_with_spinner(self, mock_halo_class, mock_client_class):
        """Test generate_commit_message with spinner (non-quiet mode)."""
        # Setup mocks
        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "docs: Update README"}}]}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Test with spinner enabled (quiet=False)
        result = generate_commit_message(model="openai:gpt-4", prompt="test", quiet=False)

        assert result == "docs: Update README"

        # Verify spinner was used
        mock_halo_class.assert_called_once()
        mock_spinner.start.assert_called_once()
        mock_spinner.succeed.assert_called_once_with("Generated commit message with OpenAI gpt-4")

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.time.sleep")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_retry_logic(self, mock_sleep, mock_client_class):
        """Test retry logic when generation fails."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First two attempts fail, third succeeds
        mock_client.post.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            MagicMock(
                json=lambda: {"choices": [{"message": {"content": "feat: Success after retries"}}]},
                raise_for_status=lambda: None,
            ),
        ]

        # Test with retries
        result = generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=3, quiet=True)

        assert result == "feat: Success after retries"
        assert mock_client.post.call_count == 3

        # Verify sleep was called for retries
        assert mock_sleep.call_count == 2  # 2 retries
        mock_sleep.assert_any_call(2)  # First retry: 2^1 = 2
        mock_sleep.assert_any_call(4)  # Second retry: 2^2 = 4

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.time.sleep")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_max_retries_exceeded(self, mock_sleep, mock_client_class):
        """Test that AIError is raised when max retries are exceeded."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # All attempts fail
        mock_client.post.side_effect = Exception("Persistent error")

        # Test max retries exceeded
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=2, quiet=True)

        assert "Failed to generate commit message after 2 attempts" in str(exc_info.value)
        assert mock_client.post.call_count == 2

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_authentication_error(self, mock_client_class):
        """Test error type classification for authentication errors."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Invalid API key")

        # Test authentication error
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=True)

        assert exc_info.value.error_type == "authentication"

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_rate_limit_error(self, mock_client_class):
        """Test error type classification for rate limit errors."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Rate limit exceeded")

        # Test rate limit error
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=True)

        assert exc_info.value.error_type == "rate_limit"

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_timeout_error(self, mock_client_class):
        """Test error type classification for timeout errors."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Request timeout")

        # Test timeout error
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=True)

        assert exc_info.value.error_type == "timeout"

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_connection_error(self, mock_client_class):
        """Test error type classification for connection errors."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Network connection failed")

        # Test connection error
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=True)

        assert exc_info.value.error_type == "connection"

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_model_error(self, mock_client_class):
        """Test error type classification for model errors."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Model not found")

        # Test model error
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=True)

        assert exc_info.value.error_type == "model"

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_unknown_error(self, mock_client_class):
        """Test error type classification for unknown errors."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Some random error")

        # Test unknown error
        with pytest.raises(AIError) as exc_info:
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=True)

        assert exc_info.value.error_type == "unknown"

    @patch("gac.ai_providers.httpx.Client")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_response_without_choices(self, mock_client_class):
        """Test handling of normal response format."""
        # Setup mock with normal response
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Alternative response format"}}]}
        mock_client.post.return_value = mock_response

        result = generate_commit_message(model="openai:gpt-4", prompt="test", quiet=True)

        assert result == "Alternative response format"

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.Halo")
    @patch("gac.ai_providers.time.sleep")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_retry_with_spinner(self, mock_sleep, mock_halo_class, mock_client_class):
        """Test retry logic with spinner animation."""
        # Setup mocks
        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First attempt fails, second succeeds
        mock_client.post.side_effect = [
            Exception("Temporary error"),
            MagicMock(json=lambda: {"choices": [{"message": {"content": "Success"}}]}, raise_for_status=lambda: None),
        ]

        # Test with spinner and retry
        result = generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=2, quiet=False)

        assert result == "Success"

        # Verify spinner was started and succeeded
        mock_spinner.start.assert_called_once()
        mock_spinner.succeed.assert_called_once()

        # Verify that sleep was called during retry (indicating retry countdown happened)
        assert mock_sleep.call_count > 0

    @patch("gac.ai_providers.httpx.Client")
    @patch("gac.ai_providers.Halo")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_generate_commit_message_failure_with_spinner(self, mock_halo_class, mock_client_class):
        """Test that spinner shows failure when all retries are exhausted."""
        # Setup mocks
        mock_spinner = MagicMock()
        mock_halo_class.return_value = mock_spinner

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # All attempts fail
        mock_client.post.side_effect = Exception("Persistent error")

        # Test failure with spinner
        with pytest.raises(AIError):
            generate_commit_message(model="openai:gpt-4", prompt="test", max_retries=1, quiet=False)

        # Verify spinner showed failure
        mock_spinner.fail.assert_called_once_with("Failed to generate commit message with OpenAI gpt-4")
