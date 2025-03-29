"""Code formatting utilities for Python files.

This module provides functions to format Python files using black and isort.
It includes functions to format individual files or all staged Python files.
"""

import logging
from typing import List

from gac.git import get_existing_staged_python_files, get_staged_python_files, stage_files
from gac.utils import run_subprocess

logger = logging.getLogger(__name__)


def run_black(python_files: List[str] = None) -> bool:
    """
    Run black code formatter on the specified Python files or all staged Python files.

    Args:
        python_files: List of Python files to format. If None, all staged Python files will be used.

    Returns:
        True if files were formatted, False otherwise
    """
    if python_files is None:
        logger.debug("Identifying Python files for formatting with black...")
        python_files = get_existing_staged_python_files()

    if not python_files:
        logger.info("No existing Python files to format with black.")
        return False

    n_before = len(python_files)
    try:
        run_subprocess(["black"] + python_files)
        logger.debug("Checking which files were modified by black...")
        formatted_files = get_staged_python_files()
        n_formatted = n_before - len(formatted_files)
        logger.info(f"Black formatted {n_formatted} files.")
        return n_formatted > 0
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False


def run_isort(python_files: List[str] = None) -> bool:
    """
    Run isort import sorter on the specified Python files or all staged Python files.

    Args:
        python_files: List of Python files to format. If None, all staged Python files will be used.

    Returns:
        True if files were formatted, False otherwise
    """
    if python_files is None:
        logger.debug("Identifying Python files for import sorting with isort...")
        python_files = get_existing_staged_python_files()

    if not python_files:
        logger.info("No existing Python files to format with isort.")
        return False

    n_before = len(python_files)
    try:
        run_subprocess(["isort"] + python_files)
        logger.debug("Checking which files were modified by isort...")
        formatted_files = get_staged_python_files()
        n_formatted = n_before - len(formatted_files)
        logger.info(f"isort formatted {n_formatted} files.")
        return n_formatted > 0
    except Exception as e:
        logger.error(f"Error running isort: {e}")
        return False


def format_staged_files(stage_after_format: bool = True) -> bool:
    """
    Format all staged Python files using black and isort.

    This function runs both black and isort on all staged Python files,
    and optionally re-stages the formatted files.

    Args:
        stage_after_format: Whether to re-stage the formatted files.

    Returns:
        True if any files were formatted, False otherwise
    """

    logger.debug("Running code formatters on staged Python files...")

    # Get the Python files that exist and are staged
    python_files = get_existing_staged_python_files()
    if not python_files:
        logger.info("No existing Python files to format.")
        return False

    # Run formatters
    black_formatted = run_black(python_files)
    isort_formatted = run_isort(python_files)

    # Re-stage files if required
    if stage_after_format and (black_formatted or isort_formatted):
        logger.debug("Re-staging Python files after formatting...")
        formatted_files = get_existing_staged_python_files()
        if formatted_files:
            stage_files(formatted_files)
            logger.info(f"Re-staged {len(formatted_files)} Python files after formatting.")

    return black_formatted or isort_formatted
