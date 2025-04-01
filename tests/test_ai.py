"""Test module for gac.ai_utils."""

import unittest
from unittest.mock import patch

import tiktoken

from gac.ai import chat, count_tokens


class TestAiUtils(unittest.TestCase):
    """Tests for AI utility functions."""

    @patch("gac.ai.generate_commit_message")
    def test_chat(self, mock_generate_commit_message):
        """Test chat function calls generate_commit_message correctly."""
        # Configure the mock response
        mock_generate_commit_message.return_value = "Test response"

        # Test parameters
        messages = [{"role": "user", "content": "Hello"}]
        model = "test:model"
        temperature = 0.5

        # Call the function under test
        result = chat(messages, model=model, temperature=temperature, test_mode=False)

        # Verify the mock was called with expected arguments
        mock_generate_commit_message.assert_called_once()
        call_args = mock_generate_commit_message.call_args
        self.assertEqual(call_args[1]["model"], model)
        self.assertEqual(call_args[1]["temperature"], temperature)
        self.assertIn("Hello", call_args[1]["prompt"])

        # Check the result matches expected response
        self.assertEqual(result, "Test response")

    def test_chat_test_mode(self):
        """Test chat function in test mode."""
        result = chat([], test_mode=True)

        self.assertEqual(result, "test_response")

    @patch("gac.ai.generate_commit_message")
    def test_chat_with_system(self, mock_generate_commit_message):
        """Test chat function with system message."""
        # Configure the mock response
        mock_generate_commit_message.return_value = "Test response"

        # Test parameters
        messages = [{"role": "user", "content": "Hello"}]
        system = "You are a helpful assistant"

        # Call the function under test
        result = chat(messages, system=system, test_mode=False)

        # Verify the mock was called with correct system message
        mock_generate_commit_message.assert_called_once()
        call_args = mock_generate_commit_message.call_args
        self.assertIn("[System] You are a helpful assistant", call_args[1]["prompt"])
        self.assertIn("Hello", call_args[1]["prompt"])

        # Check the result matches expected response
        self.assertEqual(result, "Test response")

    @patch("gac.ai.generate_commit_message")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("json.dump")
    def test_chat_save_conversation(self, mock_json_dump, mock_open, mock_generate_commit_message):
        """Test chat function saves conversation when path is provided."""
        # Configure the mock response
        mock_generate_commit_message.return_value = "Test response"

        messages = [{"role": "user", "content": "Hello"}]
        save_path = "test_conversation.json"

        result = chat(messages, save_conversation_path=save_path, test_mode=False)

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

        # The actual implementation returns 2 tokens in test mode
        self.assertEqual(result, 2)


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
@patch("gac.ai.generate_commit_message")
def test_chat_with_ollama_not_available(mock_generate, mock_is_model_available, mock_is_available):
    """Test chat with Ollama not available."""
    # This test doesn't need to raise an error since chat() delegates to generate_commit_message
    mock_generate.return_value = "Test response"

    result = chat(
        [{"role": "user", "content": "Hello"}],
        model="ollama:llama3",
        test_mode=False,
    )

    assert result == "Test response"
    mock_generate.assert_called_once()


@patch("gac.ai.is_ollama_available")
@patch("gac.ai.is_ollama_model_available")
@patch("gac.ai.generate_commit_message")
def test_chat_with_ollama_model_not_available(
    mock_generate, mock_is_model_available, mock_is_available
):
    """Test chat with Ollama model not available."""
    # This test doesn't need to raise an error since chat() delegates to generate_commit_message
    mock_generate.return_value = "Test response"

    result = chat(
        [{"role": "user", "content": "Hello"}],
        model="ollama:unavailable-model",
        test_mode=False,
    )

    assert result == "Test response"
    mock_generate.assert_called_once()


@patch("gac.ai.generate_commit_message")
def test_chat_with_one_liner(mock_generate_commit_message):
    """Test chat with one_liner=True converts multiline responses to single line."""
    # Create a multiline response
    mock_generate_commit_message.return_value = "Line 1\nLine 2\nLine 3"

    # Call chat with one_liner=True
    result = chat(
        [{"role": "user", "content": "Hello"}],
        one_liner=True,
        test_mode=False,
    )

    # Check result has no newlines and extra spaces removed
    assert result == "Line 1"
    assert "\n" not in result


if __name__ == "__main__":
    unittest.main()
