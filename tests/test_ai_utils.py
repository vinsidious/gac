"""Test module for gac.ai_utils."""

import unittest
from unittest.mock import MagicMock, patch

import pytest
import tiktoken

from gac.ai_utils import (
    APIConnectionError,
    APIUnsupportedModelError,
    chat,
    count_tokens,
    extract_model_name,
    is_ollama_available,
    is_ollama_model_available,
)


class TestAiUtils(unittest.TestCase):
    """Tests for AI utility functions."""

    @patch("gac.ai_utils.ai.Client")
    @patch("gac.ai_utils.llm_cache.get", return_value=None)  # Force cache miss
    def test_chat(self, mock_cache_get, mock_client_class):
        """Test chat function calls the AI client correctly."""
        # Create mock client and configure it
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create mock completion API
        mock_completions = MagicMock()
        mock_client.chat.completions = mock_completions

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_completions.create.return_value = mock_response

        # Test parameters
        messages = [{"role": "user", "content": "Hello"}]
        model = "test:model"
        temperature = 0.5

        # Call the function under test and force cache bypass
        result = chat(
            messages, model=model, temperature=temperature, test_mode=False, cache_skip=True
        )

        # Verify the mock was called with expected arguments
        mock_completions.create.assert_called_once()
        call_kwargs = mock_completions.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], model)
        self.assertEqual(call_kwargs["messages"], messages)
        self.assertEqual(call_kwargs["temperature"], temperature)

        # Check the result matches expected response
        self.assertEqual(result, "Test response")

    def test_chat_test_mode(self):
        """Test chat function in test mode."""
        result = chat([], test_mode=True)

        self.assertEqual(result, "test_response")

    @patch("gac.ai_utils.ai.Client")
    @patch("gac.ai_utils.llm_cache.get", return_value=None)  # Force cache miss
    def test_chat_with_system(self, mock_cache_get, mock_client_class):
        """Test chat function with system message."""
        # Create mock client and configure it
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create mock completion API
        mock_completions = MagicMock()
        mock_client.chat.completions = mock_completions

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_completions.create.return_value = mock_response

        # Test parameters
        messages = [{"role": "user", "content": "Hello"}]
        system = "You are a helpful assistant"

        # Call the function under test and force cache bypass
        result = chat(messages, system=system, test_mode=False, cache_skip=True)

        # Verify the mock was called with correct system message
        mock_completions.create.assert_called_once()
        call_kwargs = mock_completions.create.call_args.kwargs
        self.assertEqual(call_kwargs["messages"][0]["role"], "system")
        self.assertEqual(call_kwargs["messages"][0]["content"], system)
        self.assertEqual(call_kwargs["messages"][1], messages[0])

        # Check the result matches expected response
        self.assertEqual(result, "Test response")

    @patch("gac.ai_utils.ai.Client")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("json.dump")
    def test_chat_save_conversation(self, mock_json_dump, mock_open, mock_client_class):
        """Test chat function saves conversation when path is provided."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        save_path = "test_conversation.json"

        result = chat(messages, save_conversation_path=save_path)

        # Check if open was called with the correct path
        mock_open.assert_any_call(save_path, "w")

        # Verify json.dump was called (may be called multiple times due to caching)
        self.assertTrue(mock_json_dump.call_count >= 1)

        # Find the call that contains the conversation data we're looking for
        conversation_call = None
        for call in mock_json_dump.call_args_list:
            call_args = call[0][0]
            if isinstance(call_args, dict) and "messages" in call_args and "response" in call_args:
                conversation_call = call
                break

        self.assertIsNotNone(conversation_call, "No json.dump call with conversation data found")

        # Verify the saved data
        saved_data = conversation_call[0][0]
        self.assertEqual(saved_data["messages"], messages)
        self.assertEqual(saved_data["response"], "Test response")

        self.assertEqual(result, "Test response")

    def test_count_tokens_string(self):
        """Test count_tokens with string input."""
        # Use tiktoken directly to get expected token count
        encoding = tiktoken.get_encoding("cl100k_base")
        text = "Test message"
        expected = len(encoding.encode(text))

        result = count_tokens(text, "test:model")
        self.assertEqual(result, expected)

    def test_count_tokens_messages(self):
        """Test count_tokens with messages list input."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        # Use tiktoken directly to get expected token count
        encoding = tiktoken.get_encoding("cl100k_base")
        expected = len(encoding.encode("You are helpful\nHello"))

        result = count_tokens(messages, "test:model")
        self.assertEqual(result, expected)

    def test_count_tokens_test_mode(self):
        """Test count_tokens in test mode."""
        result = count_tokens("Any message", "test:model", test_mode=True)

        self.assertEqual(result, 10)


def test_extract_model_name():
    """Test the extract_model_name function."""
    assert extract_model_name("anthropic:claude-3") == "claude-3"
    assert extract_model_name("openai:gpt-4") == "gpt-4"
    assert extract_model_name("ollama:llama3.2") == "llama3.2"
    assert extract_model_name("model-without-provider") == "model-without-provider"
    assert extract_model_name("provider:with:colons") == "with:colons"


@patch("gac.ai_utils.ollama")
def test_is_ollama_available(mock_ollama):
    """Test the is_ollama_available function."""
    # Ensure mock_ollama is not None
    mock_ollama.list.return_value = {"models": []}
    assert is_ollama_available() is True

    # Test when Ollama raises an exception
    mock_ollama.list.side_effect = Exception("Connection error")
    assert is_ollama_available() is False


@patch("gac.ai_utils.ollama")
def test_is_ollama_model_available(mock_ollama):
    """Test the is_ollama_model_available function."""
    # Mock the ollama.list response
    mock_ollama.list.return_value = {
        "models": [
            {"name": "llama3.2", "size": 12345678},
            {"name": "mistral", "size": 87654321},
        ]
    }

    # Test with available model
    assert is_ollama_model_available("llama3.2") is True

    # Test with unavailable model
    assert is_ollama_model_available("nonexistent-model") is False

    # Test when Ollama raises an exception
    mock_ollama.list.side_effect = Exception("Connection error")
    assert is_ollama_model_available("llama3.2") is False


@patch("gac.ai_utils.is_ollama_available")
@patch("gac.ai_utils.is_ollama_model_available")
def test_chat_with_ollama_not_available(mock_is_model_available, mock_is_available):
    """Test chat function when Ollama is not available."""
    mock_is_available.return_value = False

    with pytest.raises(APIConnectionError) as exc_info:
        chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="ollama:llama3.2",
            cache_skip=True,
            show_spinner=False,
        )

    assert "Ollama is not available" in str(exc_info.value)
    mock_is_model_available.assert_not_called()  # Should not check model if Ollama is not available


@patch("gac.ai_utils.is_ollama_available")
@patch("gac.ai_utils.is_ollama_model_available")
def test_chat_with_ollama_model_not_available(mock_is_model_available, mock_is_available):
    """Test chat function when Ollama model is not available."""
    mock_is_available.return_value = True
    mock_is_model_available.return_value = False

    with pytest.raises(APIUnsupportedModelError) as exc_info:
        chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="ollama:nonexistent-model",
            cache_skip=True,
            show_spinner=False,
        )

    assert "Ollama model 'nonexistent-model' is not available locally" in str(exc_info.value)
    mock_is_model_available.assert_called_once_with("nonexistent-model")


if __name__ == "__main__":
    unittest.main()
