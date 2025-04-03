"""File operations module for GAC."""

import logging
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


def file_matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file matches a pattern."""
    if pattern.endswith("/*"):
        dir_pattern = pattern[:-2]
        return file_path.startswith(dir_pattern)
    elif pattern.startswith("*"):
        return file_path.endswith(pattern[1:])
    else:
        return file_path == pattern
