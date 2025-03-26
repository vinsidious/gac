"""Git-related utility functions."""

import logging
import os
import subprocess
from typing import List

from gac.utils import run_subprocess

# Set up logger
logger = logging.getLogger(__name__)


def get_staged_files() -> List[str]:
    """
    Get list of filenames of all staged files.

    Returns:
        List of staged file paths
    """
    logger.debug("Checking staged files...")
    result = run_subprocess(["git", "diff", "--staged", "--name-only"])
    return result.splitlines()


def get_staged_python_files() -> List[str]:
    """
    Get list of filenames of staged Python files.

    Returns:
        List of staged Python file paths
    """
    return [f for f in get_staged_files() if f.endswith(".py")]


def get_existing_staged_python_files() -> List[str]:
    """
    Get list of filenames of staged Python files that exist on disk.

    Returns:
        List of existing staged Python file paths
    """
    return [f for f in get_staged_python_files() if os.path.exists(f)]


def commit_changes(message: str) -> None:
    """
    Commit changes with the given message.

    Args:
        message: The commit message to use

    Raises:
        subprocess.CalledProcessError: If the git commit fails
        ValueError: If the commit message is empty
    """
    if not message:
        raise ValueError("Commit message cannot be empty")

    try:
        run_subprocess(["git", "commit", "-m", message])
    except subprocess.CalledProcessError as e:
        logger.error(f"Error committing changes: {e}")
        raise


def stage_files(files: List[str]) -> bool:
    """
    Stage files for commit.

    Args:
        files: List of files to stage

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If no files are provided
    """
    if not files:
        raise ValueError("No files provided to stage")

    try:
        result = run_subprocess(["git", "add"] + files)
        logger.info("Files staged.")
        return bool(result)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error staging files: {e}")
        return False
