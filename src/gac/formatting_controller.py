#!/usr/bin/env python3
"""Module for managing file formatting operations."""

import logging
from typing import Dict, List, Optional, Set

from gac.errors import FormattingError, convert_exception, handle_error
from gac.formatting import run_black, run_gofmt, run_isort, run_prettier, run_rustfmt
from gac.utils import print_info, print_success, print_warning

logger = logging.getLogger(__name__)


class FormattingController:
    """Controller class for managing file formatting operations."""

    def __init__(self):
        """Initialize the FormattingController."""
        # Define file extensions for each formatter
        self.python_extensions = {".py"}
        self.js_extensions = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css"}
        self.rust_extensions = {".rs"}
        self.go_extensions = {".go"}

        # Map formatters to their extensions
        self.formatter_extensions = {
            "black": self.python_extensions,
            "isort": self.python_extensions,
            "prettier": self.js_extensions,
            "rustfmt": self.rust_extensions,
            "gofmt": self.go_extensions,
        }

    def format_staged_files(
        self, staged_files: Dict[str, str], quiet: bool = False
    ) -> Dict[str, List[str]]:
        """
        Format staged files using appropriate formatters.

        Args:
            staged_files: Dictionary of staged files with status
            quiet: If True, suppress non-error output

        Returns:
            Dictionary mapping formatter names to lists of formatted files
        """
        if not staged_files:
            return {}

        # Collect files by extension
        files_by_extension = self._group_files_by_extension(staged_files)

        # Skip if no files to format
        if not any(files_by_extension.values()):
            return {}

        # Format files by type
        formatted_files = {}

        # Format Python files with black and isort
        python_files = files_by_extension.get(".py", [])
        if python_files:
            formatted_files.update(self._format_python_files(python_files, quiet))

        # Format JS/TS files with prettier
        js_files = self._get_files_with_extensions(files_by_extension, self.js_extensions)
        if js_files:
            formatted_files.update(self._format_js_files(js_files, quiet))

        # Format Rust files with rustfmt
        rust_files = files_by_extension.get(".rs", [])
        if rust_files:
            formatted_files.update(self._format_rust_files(rust_files, quiet))

        # Format Go files with gofmt
        go_files = files_by_extension.get(".go", [])
        if go_files:
            formatted_files.update(self._format_go_files(go_files, quiet))

        # Display formatted file count by formatter
        if not quiet:
            self._display_formatted_summary(formatted_files)

        return formatted_files

    def _group_files_by_extension(self, staged_files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Group staged files by their file extension.

        Args:
            staged_files: Dictionary of staged files with status or list of file paths

        Returns:
            Dictionary mapping file extensions to lists of file paths
        """
        files_by_extension = {}

        # Handle both dictionary and list inputs
        if isinstance(staged_files, dict):
            # Process dictionary input (path -> status)
            for file_path, status in staged_files.items():
                # Skip deleted files
                if status == "D":
                    continue

                # Get file extension
                extension = self._get_file_extension(file_path)
                if extension:
                    if extension not in files_by_extension:
                        files_by_extension[extension] = []
                    files_by_extension[extension].append(file_path)
        else:
            # Process list input (just file paths)
            for file_path in staged_files:
                # Get file extension
                extension = self._get_file_extension(file_path)
                if extension:
                    if extension not in files_by_extension:
                        files_by_extension[extension] = []
                    files_by_extension[extension].append(file_path)

        return files_by_extension

    def _get_file_extension(self, file_path: str) -> Optional[str]:
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

    def _get_files_with_extensions(
        self, files_by_extension: Dict[str, List[str]], extensions: Set[str]
    ) -> List[str]:
        """
        Get all files with the specified extensions.

        Args:
            files_by_extension: Dictionary mapping extensions to file lists
            extensions: Set of extensions to include

        Returns:
            List of file paths with the specified extensions
        """
        result = []
        for ext in extensions:
            if ext in files_by_extension:
                result.extend(files_by_extension[ext])
        return result

    def _format_python_files(self, files: List[str], quiet: bool = False) -> Dict[str, List[str]]:
        """
        Format Python files using black and isort.

        Args:
            files: List of Python files to format
            quiet: If True, suppress non-error output

        Returns:
            Dictionary mapping formatter names to lists of formatted files
        """
        formatted = {"black": [], "isort": []}

        if not files:
            return formatted

        if not quiet:
            print_info(f"💅 Formatting {len(files)} Python files...")

        try:
            # Format with isort
            isort_result = run_isort(files)
            if isort_result:
                formatted["isort"] = files

            # Format with black
            black_result = run_black(files)
            if black_result:
                formatted["black"] = files

        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format Python files")
            handle_error(error, quiet=quiet, exit_program=False)

        return formatted

    def _format_js_files(self, files: List[str], quiet: bool = False) -> Dict[str, List[str]]:
        """
        Format JavaScript/TypeScript files using prettier.

        Args:
            files: List of JS/TS files to format
            quiet: If True, suppress non-error output

        Returns:
            Dictionary mapping formatter names to lists of formatted files
        """
        formatted = {"prettier": []}

        if not files:
            return formatted

        if not quiet:
            print_info(f"💅 Formatting {len(files)} JS/TS files...")

        try:
            prettier_result = run_prettier(files)
            if prettier_result:
                formatted["prettier"] = files

        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format JS/TS files")
            handle_error(error, quiet=quiet, exit_program=False)

        return formatted

    def _format_rust_files(self, files: List[str], quiet: bool = False) -> Dict[str, List[str]]:
        """
        Format Rust files using rustfmt.

        Args:
            files: List of Rust files to format
            quiet: If True, suppress non-error output

        Returns:
            Dictionary mapping formatter names to lists of formatted files
        """
        formatted = {"rustfmt": []}

        if not files:
            return formatted

        if not quiet:
            print_info(f"💅 Formatting {len(files)} Rust files...")

        try:
            rustfmt_result = run_rustfmt(files)
            if rustfmt_result:
                formatted["rustfmt"] = files

        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format Rust files")
            handle_error(error, quiet=quiet, exit_program=False)

        return formatted

    def _format_go_files(self, files: List[str], quiet: bool = False) -> Dict[str, List[str]]:
        """
        Format Go files using gofmt.

        Args:
            files: List of Go files to format
            quiet: If True, suppress non-error output

        Returns:
            Dictionary mapping formatter names to lists of formatted files
        """
        formatted = {"gofmt": []}

        if not files:
            return formatted

        if not quiet:
            print_info(f"💅 Formatting {len(files)} Go files...")

        try:
            gofmt_result = run_gofmt(files)
            if gofmt_result:
                formatted["gofmt"] = files

        except Exception as e:
            error = convert_exception(e, FormattingError, "Failed to format Go files")
            handle_error(error, quiet=quiet, exit_program=False)

        return formatted

    def _display_formatted_summary(self, formatted_files: Dict[str, List[str]]) -> None:
        """
        Display a summary of formatted files by formatter.

        Args:
            formatted_files: Dictionary mapping formatter names to lists of formatted files
        """
        total_files = sum(len(files) for files in formatted_files.values())

        if total_files == 0:
            print_warning("No files were formatted")
            return

        print_success(f"Formatted {total_files} files:")

        for formatter, files in formatted_files.items():
            if files:
                print_info(f"  - {formatter}: {len(files)} files")
