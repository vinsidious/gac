"""Module for code formatting.

This module centralizes all formatting operations into a single, simpler interface.
"""

import logging
import os
import subprocess
from typing import Dict, List, Optional

from gac.errors import FormattingError, convert_exception, handle_error
from gac.utils import print_info, print_success

logger = logging.getLogger(__name__)


def run_formatter(command: List[str], files: List[str], formatter_name: str) -> bool:
    """
    Run a formatter command on the specified files.

    Args:
        command: Base command to run (e.g., ["black"])
        files: List of files to format
        formatter_name: Name of the formatter for logging

    Returns:
        True if formatting succeeded, False otherwise
    """
    if not files:
        return False

    try:
        full_command = command + files
        logger.debug(f"Running {formatter_name}: {' '.join(full_command)}")

        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
        )

        if result.returncode == 0:
            return True
        else:
            logger.warning(
                f"{formatter_name} failed with exit code {result.returncode}: {result.stderr.strip()}"
            )
            return False
    except Exception as e:
        logger.error(f"Error running {formatter_name}: {e}")
        return False


def run_black(files: List[str]) -> bool:
    """
    Format Python files with black.

    Args:
        files: List of Python files to format

    Returns:
        True if formatting succeeded, False otherwise
    """
    return run_formatter(["black"], files, "black")


def run_isort(files: List[str]) -> bool:
    """
    Format Python imports with isort.

    Args:
        files: List of Python files to sort imports for

    Returns:
        True if formatting succeeded, False otherwise
    """
    return run_formatter(["isort"], files, "isort")


def run_prettier(files: List[str]) -> bool:
    """
    Format files with prettier.

    Args:
        files: List of files to format with prettier

    Returns:
        True if formatting succeeded, False otherwise
    """
    # Check if prettier is installed
    try:
        result = subprocess.run(
            ["prettier", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.warning("Prettier is not installed or not in PATH")
            return False
    except Exception:
        logger.warning("Prettier is not installed or not in PATH")
        return False

    return run_formatter(["prettier", "--write"], files, "prettier")


def run_rustfmt(files: List[str]) -> bool:
    """
    Format Rust files with rustfmt.

    Args:
        files: List of Rust files to format

    Returns:
        True if formatting succeeded, False otherwise
    """
    return run_formatter(["rustfmt"], files, "rustfmt")


def run_gofmt(files: List[str]) -> bool:
    """
    Format Go files with gofmt.

    Args:
        files: List of Go files to format

    Returns:
        True if formatting succeeded, False otherwise
    """
    if not files:
        return False

    try:
        # gofmt behaves differently from other formatters, handling one file at a time
        for file in files:
            logger.debug(f"Running gofmt on {file}")
            result = subprocess.run(
                ["gofmt", "-w", file],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.warning(f"gofmt failed on {file}: {result.stderr.strip()}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error running gofmt: {e}")
        return False


def _get_file_extension(file_path: str) -> Optional[str]:
    """
    Get the file extension from a file path.

    Args:
        file_path: Path to the file

    Returns:
        File extension with dot (e.g., '.py') or None if no extension
    """
    parts = file_path.split(".")
    if len(parts) > 1:
        return f".{parts[-1]}"
    return None


def _group_files_by_extension(files: List[str]) -> Dict[str, List[str]]:
    """
    Group files by their extension.

    Args:
        files: List of file paths

    Returns:
        Dictionary mapping extensions to lists of file paths
    """
    files_by_extension = {}

    for file_path in files:
        # Skip files that don't exist
        if not os.path.exists(file_path):
            continue

        # Get file extension
        extension = _get_file_extension(file_path)
        if extension:
            if extension not in files_by_extension:
                files_by_extension[extension] = []
            files_by_extension[extension].append(file_path)

    return files_by_extension


def format_files(files: List[str], quiet: bool = False) -> Dict[str, List[str]]:
    """
    Format files using appropriate formatters based on file extension.

    Args:
        files: List of files to format
        quiet: If True, suppress output

    Returns:
        Dictionary mapping formatter names to lists of formatted files
    """
    if not files:
        return {}

    # Define file extensions for each formatter
    js_extensions = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css"}

    # Group files by extension
    files_by_extension = _group_files_by_extension(files)

    # Skip if no files to format
    if not any(files_by_extension.values()):
        return {}

    # Format files by type
    formatted_files = {}

    # Format Python files with black and isort
    python_files = files_by_extension.get(".py", [])
    if python_files:
        if not quiet:
            print_info(f"Formatting {len(python_files)} Python files...")

        try:
            # Format with isort
            isort_result = run_isort(python_files)
            if isort_result:
                formatted_files["isort"] = python_files

            # Format with black
            black_result = run_black(python_files)
            if black_result:
                formatted_files["black"] = python_files
        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format Python files")
            handle_error(error, quiet=quiet, exit_program=False)

    # Format JS/TS files with prettier
    js_files = []
    for ext in js_extensions:
        if ext in files_by_extension:
            js_files.extend(files_by_extension[ext])

    if js_files:
        if not quiet:
            print_info(f"Formatting {len(js_files)} JavaScript/TypeScript files...")

        try:
            prettier_result = run_prettier(js_files)
            if prettier_result:
                formatted_files["prettier"] = js_files
        except Exception as e:
            error = convert_exception(
                e, FormattingError, "Failed to format JavaScript/TypeScript files"
            )
            handle_error(error, quiet=quiet, exit_program=False)

    # Format Rust files with rustfmt
    rust_files = files_by_extension.get(".rs", [])
    if rust_files:
        if not quiet:
            print_info(f"Formatting {len(rust_files)} Rust files...")

        try:
            rustfmt_result = run_rustfmt(rust_files)
            if rustfmt_result:
                formatted_files["rustfmt"] = rust_files
        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format Rust files")
            handle_error(error, quiet=quiet, exit_program=False)

    # Format Go files with gofmt
    go_files = files_by_extension.get(".go", [])
    if go_files:
        if not quiet:
            print_info(f"Formatting {len(go_files)} Go files...")

        try:
            gofmt_result = run_gofmt(go_files)
            if gofmt_result:
                formatted_files["gofmt"] = go_files
        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format Go files")
            handle_error(error, quiet=quiet, exit_program=False)

    # Display formatted file count
    if formatted_files and not quiet:
        # Use a set to count unique files (avoiding double-counting Python files formatted by both black and isort)
        unique_files = set()
        for files in formatted_files.values():
            unique_files.update(files)
        formatted_count = len(unique_files)
        print_success(f"Formatted {formatted_count} files")

    return formatted_files
