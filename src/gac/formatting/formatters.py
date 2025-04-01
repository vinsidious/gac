"""
Compatibility module for formatters.

This module is maintained for backward compatibility with tests.
New code should use the format.py module directly.
"""

import logging
import os
from typing import Dict, List, Optional

# For backward compatibility with test patching
# These need to be imported for tests that patch them
from gac.format import format_files as format_staged_files  # noqa
from gac.format import run_black, run_gofmt, run_isort, run_prettier, run_rustfmt  # noqa

logger = logging.getLogger(__name__)


# For backward compatibility with test patching
def _get_file_extension(file_path: str) -> Optional[str]:
    """Get the file extension from a file path."""
    return os.path.splitext(file_path)[1]


def _group_files_by_extension(files: List[str]) -> Dict[str, List[str]]:
    """Group files by their extension."""
    from gac.format import _group_files_by_extension as group_files

    return group_files(files)
