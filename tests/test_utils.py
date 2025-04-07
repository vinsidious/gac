"""Tests for gac.utils module."""

import pytest

from gac.utils import file_matches_pattern


class TestUtils:
    """Tests for utility functions."""

    @pytest.mark.parametrize(
        "file_path,pattern,expected",
        [
            # Exact matches
            ("file.py", "file.py", True),
            ("file.py", "other.py", False),
            ("path/to/file.py", "path/to/file.py", True),
            # Directory wildcards
            ("src/file.py", "src/*", True),
            ("src/nested/file.py", "src/*", True),
            ("docs/file.md", "src/*", False),
            # Extension wildcards
            ("file.py", "*.py", True),
            ("src/file.py", "*.py", True),
            ("file.js", "*.py", False),
        ],
    )
    def test_file_matches_pattern(self, file_path: str, pattern: str, expected: bool):
        """Test file_matches_pattern function with various patterns."""
        result = file_matches_pattern(file_path, pattern)
        assert result == expected
