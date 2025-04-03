"""
Tests for utility functions in gac.utils module.
"""

from unittest.mock import patch

from gac.utils import print_message


def test_print_functions():
    """Test that print utility functions work correctly."""
    with patch("gac.utils.console.print") as mock_console_print:
        print_message("Info message", level="info")
        mock_console_print.assert_called_with("Info message", style="info")

        print_message("Success message", level="success")
        mock_console_print.assert_called_with("Success message", style="success")

        print_message("Warning message", level="warning")
        mock_console_print.assert_called_with("Warning message", style="warning")

        print_message("Error message", level="error")
        mock_console_print.assert_called_with("Error message", style="error")

        print_message("Custom message", level="notification")
        mock_console_print.assert_called_with("Custom message", style="notification")
