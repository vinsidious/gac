"""
Tests for utility functions in gac.utils module.
"""

from unittest.mock import MagicMock, patch

import pytest

from gac.utils import Spinner, print_error, print_info, print_message, print_success, print_warning


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


def test_spinner_context_manager():
    """Test that the Spinner context manager works correctly."""
    mock_halo = MagicMock()

    with patch("gac.utils.Halo", return_value=mock_halo):
        with Spinner("Test message") as spinner:
            # Check that spinner was started
            mock_halo.start.assert_called_once()

            # Test message update
            spinner.update_message("Updated message")
            assert mock_halo.text == "Updated message..."

        # Check that spinner was stopped after context exit
        mock_halo.stop.assert_called_once()


def test_spinner_initialization():
    """Test that the Spinner initializes with correct parameters."""
    with patch("gac.utils.Halo") as mock_halo_class:
        _ = Spinner("Test message")

        # Verify Halo was initialized with correct parameters
        mock_halo_class.assert_called_once()
        args, kwargs = mock_halo_class.call_args

        # Check that text parameter is correctly formatted
        assert kwargs["text"] == "Test message..."

        # Verify spinner type and color
        assert kwargs["spinner"] == "dots"
        assert kwargs["color"] == "cyan"  # Ensure it uses a valid color, not 'rainbow'


def test_spinner_color_validity():
    """Test that the spinner uses a valid color that won't cause KeyError."""
    # This is an integration test that actually creates a Halo instance
    # to verify that the color we're using is valid
    try:
        from halo import Halo

        spinner = Halo(text="Testing...", spinner="dots", color="cyan")
        # If this doesn't raise an exception, the color is valid
        assert spinner is not None
    except KeyError as e:
        pytest.fail(f"Invalid color for Halo spinner caused KeyError: {e}")
