"""Test module for gac.ai_utils."""

import unittest
from unittest.mock import MagicMock, patch

import pytest
import tiktoken

from gac.ai import (
    AIConnectionError,
    AIModelError,
    chat,
    count_tokens,
    extract_provider_and_model,
    is_ollama_available,
    is_ollama_model_available,
)


class TestAiUtils(unittest.TestCase):
    """Tests for AI utility functions."""

    @patch("gac.ai.Client")
    def test_chat(self, mock_client):
        """Test chat function calls the AI client correctly."""
        # Create mock client and configure it
        mock_client = MagicMock()

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

        # Call the function under test
        result = chat(messages, model=model, temperature=temperature, test_mode=False)

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

    @patch("gac.ai.Client")
    def test_chat_with_system(self, mock_client):
        """Test chat function with system message."""
        # Create mock client and configure it
        mock_client = MagicMock()

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

        # Call the function under test
        result = chat(messages, system=system, test_mode=False)

        # Verify the mock was called with correct system message
        mock_completions.create.assert_called_once()
        call_kwargs = mock_completions.create.call_args.kwargs
        self.assertEqual(call_kwargs["messages"][0]["role"], "system")
        self.assertEqual(call_kwargs["messages"][0]["content"], system)
        self.assertEqual(call_kwargs["messages"][1], messages[0])

        # Check the result matches expected response
        self.assertEqual(result, "Test response")

    @patch("gac.ai.Client")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("json.dump")
    def test_chat_save_conversation(self, mock_json_dump, mock_open, mock_client):
        """Test chat function saves conversation when path is provided."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        save_path = "test_conversation.json"

        result = chat(messages, save_conversation_path=save_path)

        # Check if open was called with the correct path
        mock_open.assert_any_call(save_path, "w")

        # Verify json.dump was called
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
    assert extract_provider_and_model("anthropic:claude-3") == ("anthropic", "claude-3")
    assert extract_provider_and_model("openai:gpt-4") == ("openai", "gpt-4")
    assert extract_provider_and_model("ollama:llama3.2") == ("ollama", "llama3.2")
    # Default provider should be anthropic
    assert extract_provider_and_model("model-without-provider") == (
        "anthropic",
        "model-without-provider",
    )
    # Handle multiple colons
    assert extract_provider_and_model("provider:with:colons") == ("provider", "with:colons")


@patch("gac.ai.ollama")
def test_is_ollama_available(mock_ollama):
    """Test the is_ollama_available function."""
    # Ensure mock_ollama is not None
    mock_ollama.list.return_value = {"models": []}
    assert is_ollama_available() is True

    # Test when Ollama raises an exception
    mock_ollama.list.side_effect = Exception("Connection error")
    assert is_ollama_available() is False


@patch("gac.ai.ollama")
def test_is_ollama_model_available(mock_ollama):
    """Test the is_ollama_model_available function."""
    # Mock the ollama.list response
    mock_ollama.list.return_value = {
        "models": [
            {"name": "llama3"},
            {"name": "mistral"},
            {"name": "gemma"},
        ]
    }

    # Test with available model
    assert is_ollama_model_available("llama3") is True

    # Test with unavailable model
    assert is_ollama_model_available("unavailable-model") is False


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
def test_chat_with_ollama_not_available(mock_is_model_available, mock_is_available):
    """Test chat raises APIConnectionError when Ollama is not available."""
    mock_is_available.return_value = False
    mock_is_model_available.return_value = False

    with pytest.raises(AIConnectionError) as e:
        chat(
            [{"role": "user", "content": "Hello"}],
            model="ollama:llama3",
            test_mode=False,
        )

    assert "not available" in str(e.value)


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
def test_chat_with_ollama_model_not_available(mock_is_model_available, mock_is_available):
    """Test chat raises APIUnsupportedModelError when Ollama model is not available."""
    mock_is_available.return_value = True
    mock_is_model_available.return_value = False

    with pytest.raises(AIModelError) as e:
        chat(
            [{"role": "user", "content": "Hello"}],
            model="ollama:unavailable-model",
            test_mode=False,
        )

    assert "not available locally" in str(e.value)


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
@patch("gac.ai.ollama")
def test_chat_with_ollama_direct(mock_ollama, mock_is_model_available, mock_is_available):
    """Test chat uses Ollama directly when provider is ollama."""
    # Setup mocks
    mock_is_available.return_value = True
    mock_is_model_available.return_value = True
    mock_ollama.chat.return_value = {"message": {"content": "Ollama response"}}

    # Test parameters
    messages = [{"role": "user", "content": "Hello"}]
    model = "ollama:llama3"

    # Call the function
    result = chat(
        messages,
        model=model,
        test_mode=False,
        show_spinner=False,  # Disable spinner to simplify test
    )

    # Verify Ollama was called correctly
    mock_ollama.chat.assert_called_once()
    call_args = mock_ollama.chat.call_args
    assert call_args[1]["model"] == "llama3"
    assert call_args[1]["messages"] == messages

    # Check the result
    assert result == "Ollama response"


@patch("gac.ai.Client")
def test_chat_with_one_liner(mock_client):
    """Test chat with one_liner=True converts multiline responses to single line."""
    # Create mock client and response
    mock_client = MagicMock()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    # Create a multiline response
    mock_response.choices[0].message.content = "Line 1\nLine 2\nLine 3"
    mock_client.chat.completions.create.return_value = mock_response

    # Call chat with one_liner=True
    result = chat(
        [{"role": "user", "content": "Hello"}],
        one_liner=True,
        test_mode=False,
    )

    # Check result has no newlines and extra spaces removed
    assert result == "Line 1 Line 2 Line 3"
    assert "\n" not in result


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
@patch("gac.ai.ollama")
def test_chat_with_ollama_one_liner(mock_ollama, mock_is_model_available, mock_is_available):
    """Test chat with Ollama and one_liner=True."""
    # Setup mocks
    mock_is_available.return_value = True
    mock_is_model_available.return_value = True
    # Create a multiline response
    mock_ollama.chat.return_value = {"message": {"content": "Line 1\nLine 2\nLine 3"}}

    # Call chat with one_liner=True
    result = chat(
        [{"role": "user", "content": "Hello"}],
        model="ollama:llama3",
        one_liner=True,
        test_mode=False,
        show_spinner=False,  # Disable spinner to simplify test
    )

    # Check result has no newlines and extra spaces removed
    assert result == "Line 1 Line 2 Line 3"
    assert "\n" not in result


if __name__ == "__main__":
    unittest.main()
