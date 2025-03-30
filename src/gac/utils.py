"""Utility functions for the gac package."""

import logging
import subprocess
from enum import Enum
from typing import List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)

# Initialize a console for rich output
console = Console()


class Color(Enum):
    """Color codes for terminal output."""

    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    BRIGHT_BLACK = 8
    BRIGHT_RED = 9
    BRIGHT_GREEN = 10
    BRIGHT_YELLOW = 11
    BRIGHT_BLUE = 12
    BRIGHT_MAGENTA = 13
    BRIGHT_CYAN = 14
    BRIGHT_WHITE = 15


def colorize(text: str, fg_color: Color = None, bg_color: Color = None, bold: bool = False) -> str:
    """
    Apply colors to text for terminal output.

    Args:
        text: The text to colorize
        fg_color: Foreground color from the Color enum
        bg_color: Background color from the Color enum
        bold: Whether to make the text bold

    Returns:
        The colorized text string
    """
    # Don't colorize if no colors are specified
    if fg_color is None and bg_color is None and not bold:
        return text

    # Use click's style function for coloring
    return click.style(
        text,
        fg=fg_color.name.lower() if fg_color else None,
        bg=bg_color.name.lower() if bg_color else None,
        bold=bold,
    )


def print_info(message: str) -> None:
    """Print an info message in blue."""
    console.print(f"[blue]ℹ️ {message}[/blue]")


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[green]✅ {message}[/green]")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[yellow]⚠️ {message}[/yellow]")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[red]❌ {message}[/red]")


def print_header(message: str) -> None:
    """Print a header message in bold cyan."""
    console.print(f"[bold cyan]== {message} ==[/bold cyan]")


def format_bordered_text(
    content: str, header: str = None, min_length: int = 0, max_length: int = 120
) -> str:
    """
    Format text with a border and optional header.

    Args:
        content: The text content to display
        header: Optional header text to display in the border
        min_length: Minimum border length (default: 0)
        max_length: Maximum border length (default: 120)

    Returns:
        Formatted text with borders
    """
    # Get the longest line length
    max_line_length = max(len(line) for line in content.split("\n"))
    # Calculate border length
    border_length = max(min_length, max_line_length)
    # Cap at max_length
    border_length = min(border_length, max_length)

    if header:
        # Calculate padding ensuring equal sides by rounding up
        total_padding = border_length - len(header)
        left_padding = (total_padding + 1) // 2
        right_padding = left_padding
        top_border = f"{'=' * left_padding}{header}{'=' * right_padding}"
        bottom_border = "=" * len(top_border)
    else:
        # Simple border without header
        top_border = "=" * border_length
        bottom_border = top_border

    return f"\n{top_border}\n{content}\n{bottom_border}\n"


def run_subprocess(command: List[str], check: bool = False) -> str:
    """
    Run a subprocess and return its output.

    Args:
        command: List of command components
        check: Whether to check return code

    Returns:
        Output of the command

    Raises:
        subprocess.CalledProcessError: If check=True and the command fails
    """
    try:
        logger.debug(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            raise
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(f"Error: {e.stderr.strip() if e.stderr else str(e)}")
        return ""
