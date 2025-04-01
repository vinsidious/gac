"""Tests for the errors module."""

import unittest
from unittest.mock import patch

from gac.errors import (
    AIError,
    ConfigError,
    FormattingError,
    GACError,
    GitError,
    convert_exception,
    format_error_for_user,
    handle_error,
)


class TestErrors(unittest.TestCase):
    """Tests for error handling functionality."""

    def test_error_inheritance(self):
        """Test error class inheritance structure."""
        # GACError is the base class
        self.assertTrue(issubclass(GACError, Exception))

        # Direct subclasses of GACError
        self.assertTrue(issubclass(ConfigError, GACError))
        self.assertTrue(issubclass(GitError, GACError))
        self.assertTrue(issubclass(AIError, GACError))
        self.assertTrue(issubclass(FormattingError, GACError))

    def test_error_exit_codes(self):
        """Test that error classes have unique exit codes."""
        # Check exit codes are defined and unique
        exit_codes = {
            GACError: 1,
            ConfigError: 2,
            GitError: 3,
            AIError: 4,
            FormattingError: 5,
        }

        for error_class, expected_code in exit_codes.items():
            self.assertEqual(error_class.exit_code, expected_code)

        # Check that instances inherit the exit code
        for error_class, expected_code in exit_codes.items():
            error = error_class("Test message")
            self.assertEqual(error.exit_code, expected_code)

        # Test overriding exit code in constructor
        error = GACError("Test message", exit_code=42)
        self.assertEqual(error.exit_code, 42)

    @patch("sys.exit")
    @patch("gac.errors.logger")
    @patch("gac.errors.console.print")
    def test_handle_error(self, mock_print, mock_logger, mock_exit):
        """Test handle_error function."""
        # Test with GACError
        error = ConfigError("Configuration error")
        handle_error(error, exit_program=True)

        mock_logger.error.assert_called_with("Configuration error")
        mock_print.assert_called_with("❌ Configuration error", style="bold red")
        mock_exit.assert_called_with(2)

        # Test with standard Exception
        mock_logger.reset_mock()
        mock_print.reset_mock()
        mock_exit.reset_mock()

        error = ValueError("Invalid value")
        handle_error(error, exit_program=True)

        mock_logger.error.assert_called_with("Unexpected error: Invalid value")
        mock_print.assert_called_with("❌ Unexpected error: Invalid value", style="bold red")
        mock_exit.assert_called_with(1)

        # Test with quiet mode
        mock_logger.reset_mock()
        mock_print.reset_mock()
        mock_exit.reset_mock()

        error = ConfigError("Configuration error")
        handle_error(error, quiet=True, exit_program=True)

        mock_logger.error.assert_called_with("Configuration error")
        mock_print.assert_not_called()
        mock_exit.assert_called_with(2)

        # Test without exit
        mock_logger.reset_mock()
        mock_print.reset_mock()
        mock_exit.reset_mock()

        error = ConfigError("Configuration error")
        handle_error(error, exit_program=False)

        mock_logger.error.assert_called_with("Configuration error")
        mock_print.assert_called_with("❌ Configuration error", style="bold red")
        mock_exit.assert_not_called()

    def test_format_error_for_user(self):
        """Test format_error_for_user function."""
        # Test with AI error
        error = AIError("Failed to connect to API")
        message = format_error_for_user(error)
        self.assertIn("Failed to connect to API", message)
        self.assertIn("check your API key", message)

        # Test with standard Exception
        error = Exception("Unknown error")
        message = format_error_for_user(error)
        self.assertIn("Unknown error", message)
        self.assertIn("report it as a bug", message)

        # Test with all error types to ensure they have remediation steps
        errors = {
            AIError: "AI provider error",
            ConfigError: "Invalid configuration",
            GitError: "Git error",
            FormattingError: "Formatting failed",
        }

        for error_class, msg in errors.items():
            error = error_class(msg)
            formatted = format_error_for_user(error)
            self.assertIn(msg, formatted)
            self.assertGreater(
                len(formatted), len(msg), f"No remediation steps for {error_class.__name__}"
            )

    def test_convert_exception(self):
        """Test convert_exception function."""
        # Test with default message
        orig_error = ValueError("Invalid value")
        converted = convert_exception(orig_error, ConfigError)

        self.assertIsInstance(converted, ConfigError)
        self.assertEqual(str(converted), "Invalid value")

        # Test with custom message
        orig_error = ValueError("Invalid value")
        converted = convert_exception(orig_error, GitError, "Custom git error")

        self.assertIsInstance(converted, GitError)
        self.assertEqual(str(converted), "Custom git error")


if __name__ == "__main__":
    unittest.main()
