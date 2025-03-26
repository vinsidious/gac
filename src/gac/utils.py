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
