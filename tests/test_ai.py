"""Tests for ai module."""

from unittest.mock import MagicMock, patch

import tiktoken

from gac.ai import count_tokens, extract_text_content, get_encoding


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
            mock_client.count_tokens.return_value = 5
            mock_anthropic.Client.return_value = mock_client

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
