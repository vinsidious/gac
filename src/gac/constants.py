"""Constants for the Git Auto Commit (GAC) project."""

from enum import Enum


class FileStatus(Enum):
    """File status for Git operations."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "?"


# Default values for environment variables
DEFAULT_MAX_RETRIES = 3
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_OUTPUT_TOKENS = 256

# Logging Constants
DEFAULT_LOG_LEVEL = "WARNING"
LOGGING_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]

# Utility Constants
DEFAULT_ENCODING = "cl100k_base"
