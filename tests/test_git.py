"""Test module for gac.git."""

import unittest
from unittest.mock import patch

from gac.git import (
    FileStatus,
    commit_changes,
    get_git_operations,
    get_project_description,
    get_staged_files,
    is_large_file,
    set_git_operations,
    stage_files,
)

if __name__ == "__main__":
    unittest.main()
