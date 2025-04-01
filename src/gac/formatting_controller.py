"""
Compatibility module for formatting controller.

This module is maintained for backward compatibility with tests.
New code should use the format.py module directly.
"""

import logging
from typing import Dict, List, Optional, Set

from gac.format import format_files

logger = logging.getLogger(__name__)


class FormattingController:
    """Compatibility class for FormattingController.

    This class is provided for backward compatibility with tests.
    New code should use the format.py functions directly.
    """

    def __init__(self):
        """Initialize the FormattingController."""
        pass

    def format_staged_files(self, staged_files, quiet: bool = False) -> Dict[str, List[str]]:
        """Format staged files using appropriate formatters."""
        # If staged_files is a dict, extract file paths
        if isinstance(staged_files, dict):
            # Process dictionary input (path -> status)
            files = []
            for file_path, status in staged_files.items():
                # Skip deleted files
                if status != "D":
                    files.append(file_path)
        else:
            files = staged_files

        # Forward to the new format_files function
        return format_files(files, quiet)
