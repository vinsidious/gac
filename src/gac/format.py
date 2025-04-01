"""Code formatting module for GAC.

This module handles code formatting for different languages.
"""

import logging
import os
import subprocess
from typing import Dict, List

from gac.errors import FormattingError, convert_exception, handle_error
from gac.files import group_files_by_extension
from gac.utils import print_info

logger = logging.getLogger(__name__)


# Registry of formatters with their commands and file extensions
FORMATTERS = {
    "python": [
        {
            "name": "black",
            "command": ["black"],
            "extensions": [".py"],
        },
        {
            "name": "isort",
            "command": ["isort"],
            "extensions": [".py"],
        },
    ],
    "javascript": [
        {
            "name": "prettier",
            "command": ["prettier", "--write"],
            "extensions": [".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css"],
            "check_command": ["prettier", "--version"],
        },
    ],
    "rust": [
        {
            "name": "rustfmt",
            "command": ["rustfmt"],
            "extensions": [".rs"],
        },
    ],
    "go": [
        {
            "name": "gofmt",
            "command": ["gofmt", "-w"],
            "extensions": [".go"],
            "single_file": True,  # gofmt processes one file at a time
        },
    ],
}


def run_formatter(command: List[str], files: List[str], formatter_name: str) -> bool:
    """
    Run a formatter on the specified files.

    Args:
        command: The formatter command to run
        files: List of files to format
        formatter_name: Name of the formatter for logging

    Returns:
        True if formatting succeeded, False otherwise
    """
    if not files:
        return False

    try:
        logger.debug(f"Running {formatter_name} on {len(files)} files")

        # Some formatters like gofmt need to process files one at a time
        formatter_config = next(
            (f for lang in FORMATTERS.values() for f in lang if f["name"] == formatter_name), None
        )
        if formatter_config and formatter_config.get("single_file", False):
            for file in files:
                result = subprocess.run(
                    command + [file],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    logger.warning(f"{formatter_name} failed on {file}: {result.stderr.strip()}")
                    return False
            return True
        else:
            # Most formatters can handle multiple files at once
            result = subprocess.run(
                command + files,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"{formatter_name} failed: {result.stderr.strip()}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error running {formatter_name}: {e}")
        return False


def check_formatter_available(formatter_config: Dict) -> bool:
    """
    Check if a formatter is available on the system.

    Args:
        formatter_config: Formatter configuration dictionary

    Returns:
        True if formatter is available, False otherwise
    """
    check_command = formatter_config.get(
        "check_command", formatter_config["command"][:1] + ["--version"]
    )

    try:
        result = subprocess.run(
            check_command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


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

    # If files is a dict, extract file paths (for backward compatibility)
    if isinstance(files, dict):
        # Process dictionary input (path -> status)
        file_list = []
        for file_path, status in files.items():
            # Skip deleted files
            if status != "D":
                file_list.append(file_path)
        files = file_list

    # Filter to only include existing files
    files = [f for f in files if os.path.isfile(f)]

    # Group files by extension
    files_by_extension = group_files_by_extension(files)

    # Skip if no files to format
    if not any(files_by_extension.values()):
        return {}

    # Track formatted files
    formatted_files = {}

    # Process each extension with its formatters
    for language, formatter_configs in FORMATTERS.items():
        for formatter_config in formatter_configs:
            extensions = formatter_config["extensions"]
            command = formatter_config["command"]
            formatter_name = formatter_config["name"]

            # Collect files that match this formatter's extensions
            files_to_format = []
            for ext in extensions:
                if ext in files_by_extension:
                    files_to_format.extend(files_by_extension[ext])

            if not files_to_format:
                continue

            if not quiet:
                print_info(f"Formatting {len(files_to_format)} files with {formatter_name}...")

            # Check if formatter is available
            if not check_formatter_available(formatter_config):
                logger.warning(f"{formatter_name} is not installed or not in PATH")
                continue

            # Run the formatter
            try:
                formatting_result = run_formatter(command, files_to_format, formatter_name)
                if formatting_result:
                    formatted_files[formatter_name] = files_to_format
            except Exception as e:
                error = convert_exception(
                    e, FormattingError, f"Failed to format with {formatter_name}"
                )
                handle_error(error, quiet=quiet, exit_program=False)

    return formatted_files


if __name__ == "__main__":
    # Simple command-line interface for manual testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m gac.format file1 file2 ...")
        sys.exit(1)

    files_to_format = sys.argv[1:]
    result = format_files(files_to_format)

    if result:
        print(f"Formatted {sum(len(f) for f in result.values())} files:")
        for formatter, formatted in result.items():
            print(f"  - {formatter}: {len(formatted)} files")
    else:
        print("No files were formatted.")
