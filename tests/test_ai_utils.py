"""Test module for gac.ai_utils."""

import unittest
from unittest.mock import MagicMock, patch

from gac.ai_utils import chat, count_tokens


class TestAiUtils(unittest.TestCase):
    """Tests for AI utility functions."""

    @patch("gac.ai_utils.ai.Client")
    def test_chat(self, mock_client_class):
        """Test chat function calls the AI client correctly."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        model = "test:model"
        temperature = 0.5

        result = chat(messages, model=model, temperature=temperature)

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], model)
        self.assertEqual(call_kwargs["messages"], messages)
        self.assertEqual(call_kwargs["temperature"], temperature)

        self.assertEqual(result, "Test response")

    def test_chat_test_mode(self):
        """Test chat function in test mode."""
        result = chat([], test_mode=True)

        self.assertEqual(result, "test_response")

    @patch("gac.ai_utils.ai.Client")
    def test_chat_with_system(self, mock_client_class):
        """Test chat function with system message."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        system = "You are a helpful assistant"

        result = chat(messages, system=system)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(call_kwargs["messages"][0]["role"], "system")
        self.assertEqual(call_kwargs["messages"][0]["content"], system)
        self.assertEqual(call_kwargs["messages"][1], messages[0])

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

        mock_open.assert_called_once_with(save_path, "w")
        mock_json_dump.assert_called_once()

        saved_data = mock_json_dump.call_args[0][0]
        self.assertEqual(saved_data["messages"], messages)
        self.assertEqual(saved_data["response"], "Test response")

        self.assertEqual(result, "Test response")

    def test_count_tokens_string(self):
        """Test count_tokens with string input."""
        result = count_tokens("Test message", "test:model")

        self.assertEqual(result, len("Test message") // 4)

    def test_count_tokens_messages(self):
        """Test count_tokens with messages list input."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        result = count_tokens(messages, "test:model")

        expected = len("You are helpful") // 4 + len("Hello") // 4
        self.assertEqual(result, expected)

    def test_count_tokens_test_mode(self):
        """Test count_tokens in test mode."""
        result = count_tokens("Any message", "test:model", test_mode=True)

        self.assertEqual(result, 10)


if __name__ == "__main__":
    unittest.main()
