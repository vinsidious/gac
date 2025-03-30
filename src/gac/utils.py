"""Utility functions for the gac package."""

import logging
import subprocess
from typing import List

logger = logging.getLogger(__name__)


def run_subprocess(command: List[str]) -> str:
    """
    Run a subprocess command and return its output.

    Args:
        command: List of command arguments

    Returns:
        The command output as a string

    Raises:
        CalledProcessError: If the command fails
    """
    logger.debug(f"Running command: `{' '.join(command)}`")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Special case for git diff --quiet --cached --exit-code
    if command == ["git", "diff", "--quiet", "--cached", "--exit-code"]:
        # Returns True if no unstaged changes, False if there are unstaged changes
        return result.returncode == 0

    if result.returncode != 0:
        error_msg = f"Command failed with exit code {result.returncode}: {result.stderr}"
        logger.error(error_msg)
        raise subprocess.CalledProcessError(
            result.returncode, command, result.stdout, result.stderr
        )
    if result.stdout:
        logger.debug(f"Command output:\n{result.stdout}")
        return result.stdout
    return ""


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
