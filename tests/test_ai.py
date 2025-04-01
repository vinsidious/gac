"""Test module for gac.ai."""

import unittest
from unittest.mock import patch

import tiktoken

from gac.ai import chat, count_tokens


class TestAiUtils(unittest.TestCase):
    """Tests for AI utility functions."""

    @patch("gac.ai.generate_commit_message")
    def test_chat(self, mock_generate_commit_message):
        """Test chat function returns expected response from AI model."""
        # Configure the mock response
        mock_generate_commit_message.return_value = "Test response"

        # Test parameters
        messages = [{"role": "user", "content": "Hello"}]
        model = "test:model"
        temperature = 0.5

        # Call the function under test
        result = chat(messages, model=model, temperature=temperature, test_mode=False)

        # Verify the behavior: function returns the expected response
        self.assertEqual(result, "Test response")

        # Verify the function was called (this is a minimal implementation detail
        # but necessary to ensure the test is valid)
        mock_generate_commit_message.assert_called_once()

    def test_chat_test_mode(self):
        """Test chat function in test mode returns consistent test response."""
        result = chat([], test_mode=True)

        # Verify the behavior: test mode returns a consistent response
        self.assertEqual(result, "test_response")

    @patch("gac.ai.generate_commit_message")
    def test_chat_with_system(self, mock_generate_commit_message):
        """Test chat function with system message returns expected response."""
        # Configure the mock response
        mock_generate_commit_message.return_value = "Test response"

        # Test parameters
        messages = [{"role": "user", "content": "Hello"}]
        system = "You are a helpful assistant"

        # Call the function under test
        result = chat(messages, system=system, test_mode=False)

        # Verify the behavior: function returns the expected response
        self.assertEqual(result, "Test response")

        # Verify the function was called (minimal implementation detail)
        mock_generate_commit_message.assert_called_once()

    def test_count_tokens_string(self):
        """Test count_tokens with string input returns expected token count."""
        # Use tiktoken directly to get expected token count
        encoding = tiktoken.get_encoding("cl100k_base")
        text = "Test message"
        expected = len(encoding.encode(text))

        # Call the function under test
        result = count_tokens(text, "test:model")

        # Verify the behavior: function returns the correct token count
        self.assertEqual(result, expected)

    def test_count_tokens_messages(self):
        """Test count_tokens with messages list input returns expected token count."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        # Use tiktoken directly to get expected token count for comparison
        encoding = tiktoken.get_encoding("cl100k_base")
        expected = len(encoding.encode("You are helpful\nHello"))

        # Call the function under test
        result = count_tokens(messages, "test:model")

        # Verify the behavior: function returns the correct token count
        self.assertEqual(result, expected)

    def test_count_tokens_test_mode(self):
        """Test count_tokens in test mode returns consistent test value."""
        # Call the function under test
        result = count_tokens("Any message", "test:model", test_mode=True)

        # Verify the behavior: test mode returns a consistent value
        self.assertEqual(result, 2)


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
@patch("gac.ai.generate_commit_message")
def test_chat_with_ollama_not_available(mock_generate, mock_is_model_available, mock_is_available):
    """Test chat with Ollama model returns expected response."""
    # Configure the mock response
    mock_generate.return_value = "Test response"

    # Call the function under test
    result = chat(
        [{"role": "user", "content": "Hello"}],
        model="ollama:llama3",
        test_mode=False,
    )

    # Verify the behavior: function returns the expected response
    assert result == "Test response"
    mock_generate.assert_called_once()


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
@patch("gac.ai.generate_commit_message")
def test_chat_with_ollama_model_not_available(
    mock_generate, mock_is_model_available, mock_is_available
):
    """Test chat with unavailable Ollama model returns expected response."""
    # Configure the mock response
    mock_generate.return_value = "Test response"

    # Call the function under test
    result = chat(
        [{"role": "user", "content": "Hello"}],
        model="ollama:unavailable-model",
        test_mode=False,
    )

    # Verify the behavior: function returns the expected response
    assert result == "Test response"
    mock_generate.assert_called_once()


@patch("gac.ai.generate_commit_message")
def test_chat_with_one_liner(mock_generate_commit_message):
    """Test chat with one_liner=True returns only the first line of a multiline response."""
    # Configure the mock to return a multiline response
    mock_generate_commit_message.return_value = "Line 1\nLine 2\nLine 3"

    # Call the function under test with one_liner=True
    result = chat(
        [{"role": "user", "content": "Hello"}],
        one_liner=True,
        test_mode=False,
    )

    # Verify the behavior: function returns only the first line
    assert result == "Line 1"
    assert "\n" not in result


if __name__ == "__main__":
    unittest.main()
