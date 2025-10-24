"""Tests for the errors module."""

import unittest
from unittest.mock import patch

from gac.errors import (
    AIError,
    ConfigError,
    FormattingError,
    GacError,
    GitError,
    format_error_for_user,
    handle_error,
)


class TestErrors(unittest.TestCase):
    """Tests for error handling functionality."""

    def test_error_inheritance(self):
        """Test error classes follow the expected inheritance hierarchy."""
        # Verify the behavior: error classes have the expected inheritance structure
        self.assertTrue(issubclass(GacError, Exception))
        self.assertTrue(issubclass(ConfigError, GacError))
        self.assertTrue(issubclass(GitError, GacError))
        self.assertTrue(issubclass(AIError, GacError))
        self.assertTrue(issubclass(FormattingError, GacError))

    def test_error_exit_codes(self):
        """Test error classes provide appropriate exit codes."""
        # Define expected exit codes for each error type
        exit_codes = {
            GacError: 1,
            ConfigError: 2,
            GitError: 3,
            AIError: 4,
            FormattingError: 5,
        }

        # Verify the behavior: error classes have the expected exit codes
        for error_class, expected_code in exit_codes.items():
            self.assertEqual(error_class.exit_code, expected_code)

        # Verify the behavior: error instances inherit the exit code
        for error_class, expected_code in exit_codes.items():
            error = error_class("Test message")
            self.assertEqual(error.exit_code, expected_code)

        # Verify the behavior: exit code can be overridden in constructor
        error = GacError("Test message", exit_code=42)
        self.assertEqual(error.exit_code, 42)

    def test_ai_error_factory_methods(self):
        """Test AIError factory methods create the correct error types."""
        # Test authentication error
        auth_error = AIError.authentication_error("Invalid API key")
        self.assertEqual(auth_error.message, "Invalid API key")
        self.assertEqual(auth_error.error_type, "authentication")
        self.assertEqual(auth_error.error_code, 401)

        # Test connection error
        conn_error = AIError.connection_error("Network issue")
        self.assertEqual(conn_error.message, "Network issue")
        self.assertEqual(conn_error.error_type, "connection")
        self.assertEqual(conn_error.error_code, 503)

        # Test rate limit error
        rate_error = AIError.rate_limit_error("Too many requests")
        self.assertEqual(rate_error.message, "Too many requests")
        self.assertEqual(rate_error.error_type, "rate_limit")
        self.assertEqual(rate_error.error_code, 429)

        # Test timeout error
        timeout_error = AIError.timeout_error("Request timed out")
        self.assertEqual(timeout_error.message, "Request timed out")
        self.assertEqual(timeout_error.error_type, "timeout")
        self.assertEqual(timeout_error.error_code, 408)

        # Test model error
        model_error = AIError.model_error("Model not found")
        self.assertEqual(model_error.message, "Model not found")
        self.assertEqual(model_error.error_type, "model")
        self.assertEqual(model_error.error_code, 400)

    @patch("sys.exit")
    @patch("gac.errors.logger")
    @patch("gac.errors.console.print")
    def test_handle_error(self, mock_print, mock_logger, mock_exit):
        """Test handle_error function processes errors appropriately."""
        # Test with GACError
        error = ConfigError("Configuration error")
        handle_error(error, exit_program=True)

        # Verify the error is logged with the correct messages
        mock_logger.error.assert_any_call("Error: Configuration error")
        mock_logger.error.assert_any_call("An unexpected error occurred.")
        mock_logger.error.assert_any_call("Exiting program due to error.")

        # Verify sys.exit was called with 2 (ConfigError.exit_code)
        mock_exit.assert_called_once_with(2)

        # Reset mocks for next test
        mock_logger.reset_mock()
        mock_print.reset_mock()
        mock_exit.reset_mock()

        # Test with standard Exception
        error = ValueError("Invalid value")
        handle_error(error, exit_program=True)

        # Verify the error is logged with the correct messages
        mock_logger.error.assert_any_call("Error: Invalid value")
        mock_logger.error.assert_any_call("An unexpected error occurred.")
        mock_logger.error.assert_any_call("Exiting program due to error.")

        # Verify sys.exit was called with 1 (default for non-GacError)
        mock_exit.assert_called_once_with(1)

        # Reset mocks for next test
        mock_logger.reset_mock()
        mock_print.reset_mock()
        mock_exit.reset_mock()

        # Test without exit
        error = ConfigError("Configuration error")
        handle_error(error, exit_program=False)

        # Verify the error is logged with the correct messages
        mock_logger.error.assert_any_call("Error: Configuration error")
        mock_logger.error.assert_any_call("An unexpected error occurred.")

        # Verify sys.exit was not called
        mock_exit.assert_not_called()

    def test_format_error_for_user(self):
        """Test format_error_for_user provides helpful error messages."""
        # Test with AI error
        error = AIError("Failed to connect to API")
        message = format_error_for_user(error)

        # Verify the behavior: error message includes the original error
        self.assertIn("Failed to connect to API", message)

        # Verify the behavior: error message includes helpful remediation steps
        self.assertIn("check your API key", message)

        # Test with standard Exception
        error = Exception("Unknown error")
        message = format_error_for_user(error)

        # Verify the behavior: unknown errors include appropriate guidance
        self.assertIn("Unknown error", message)
        self.assertIn("report it as a bug", message)

        # Test all error types to ensure they have remediation steps
        errors = {
            AIError: "AI provider error",
            ConfigError: "Invalid configuration",
            GitError: "Git error",
            FormattingError: "Formatting failed",
        }

        for error_class, msg in errors.items():
            error = error_class(msg)
            formatted = format_error_for_user(error)

            # Verify the behavior: all error types include the original message
            self.assertIn(msg, formatted)

            # Verify the behavior: all error types include remediation steps
            self.assertGreater(len(formatted), len(msg))

    def test_format_error_authentication(self):
        """Test formatting of authentication errors."""
        error = AIError.authentication_error("Invalid API key")
        message = format_error_for_user(error)
        self.assertIn("Invalid API key", message)
        self.assertIn("check your API key", message)
        self.assertIn("ensure it is valid", message)

    def test_format_error_connection(self):
        """Test formatting of connection errors."""
        error = AIError.connection_error("Network unreachable")
        message = format_error_for_user(error)
        self.assertIn("Network unreachable", message)
        self.assertIn("check your internet connection", message)
        self.assertIn("try again", message)

    def test_format_error_rate_limit(self):
        """Test formatting of rate limit errors."""
        error = AIError.rate_limit_error("Too many requests")
        message = format_error_for_user(error)
        self.assertIn("Too many requests", message)
        self.assertIn("rate limit", message)
        self.assertIn("wait", message)

    def test_format_error_timeout(self):
        """Test formatting of timeout errors."""
        error = AIError.timeout_error("Request timed out")
        message = format_error_for_user(error)
        self.assertIn("Request timed out", message)
        self.assertIn("timed out", message)
        self.assertIn("try again", message)

    def test_format_error_model(self):
        """Test formatting of model errors."""
        error = AIError.model_error("Model not found")
        message = format_error_for_user(error)
        self.assertIn("Model not found", message)
        self.assertIn("check that the specified model exists", message)

    def test_unknown_error_factory(self):
        """Test AIError.unknown_error factory method."""
        error = AIError.unknown_error("Unknown issue")
        self.assertEqual(error.message, "Unknown issue")
        self.assertEqual(error.error_type, "unknown")
        self.assertEqual(error.error_code, 500)


if __name__ == "__main__":
    unittest.main()
