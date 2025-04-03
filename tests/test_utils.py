"""
Tests for utility functions in gac.utils module.
"""

from unittest.mock import patch

from gac.utils import print_error, print_info, print_message, print_success, print_warning


def test_print_functions():
    """Test that print utility functions work correctly."""
    with patch("gac.utils.console.print") as mock_console_print:
        print_info("Info message")
        mock_console_print.assert_called_with("Info message", style="info")

        print_success("Success message")
        mock_console_print.assert_called_with("Success message", style="success")

        print_warning("Warning message")
        mock_console_print.assert_called_with("Warning message", style="warning")

        print_error("Error message")
        mock_console_print.assert_called_with("Error message", style="error")

        print_message("Custom message", "notification")
        mock_console_print.assert_called_with("Custom message", style="notification")
