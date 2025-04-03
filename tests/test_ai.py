"""Test module for gac.ai."""

import unittest

import tiktoken

from gac.ai import count_tokens


class TestAiUtils(unittest.TestCase):
    """Tests for AI utility functions."""

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


if __name__ == "__main__":
    unittest.main()
