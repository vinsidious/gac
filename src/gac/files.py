"""File operations module for GAC."""

import logging
import os
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


def group_files_by_extension(files: List[str]) -> Dict[str, List[str]]:
    """Group files by their extension."""
    files_by_extension: Dict[str, List[str]] = {}

    for file_path in files:
        if not os.path.isfile(file_path):
            continue

        extension = os.path.splitext(file_path)[1]
        if extension:
            if extension not in files_by_extension:
                files_by_extension[extension] = []
            files_by_extension[extension].append(file_path)

    return files_by_extension


def filter_files_by_extension(files: List[str], extensions: List[str]) -> List[str]:
    """Filter files to include only those with specific extensions."""
    return [f for f in files if os.path.splitext(f)[1] in extensions]


def file_matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file matches a pattern."""
    if pattern.endswith("/*"):
        dir_pattern = pattern[:-2]
        return file_path.startswith(dir_pattern)
    elif pattern.startswith("*"):
        return file_path.endswith(pattern[1:])
    else:
        return file_path == pattern


def filter_files_by_patterns(
    files: List[str],
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> List[str]:
    """Filter files by include and exclude patterns."""
    result = files

    if include_patterns:
        result = [
            f
            for f in result
            if any(file_matches_pattern(f, pattern) for pattern in include_patterns)
        ]

    if exclude_patterns:
        result = [
            f
            for f in result
            if not any(file_matches_pattern(f, pattern) for pattern in exclude_patterns)
        ]

    return result


def process_files_in_batches(
    files: List[str],
    process_func: Callable[[List[str]], Dict[str, List[str]]],
    batch_size: int = 10,
) -> Dict[str, List[str]]:
    """Process files in batches to avoid overwhelming system resources."""
    results: Dict[str, List[str]] = {}

    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        batch_results = process_func(batch)

        for key, value in batch_results.items():
            if key not in results:
                results[key] = []
            results[key].extend(value)

    return results


def filter_large_files(
    files: List[str], size_check_func: Callable[[str], bool]
) -> Tuple[List[str], List[str]]:
    """Split files into normal and large files based on a size check function."""
    normal_files = []
    large_files = []

    for file_path in files:
        if size_check_func(file_path):
            large_files.append(file_path)
        else:
            normal_files.append(file_path)

    return normal_files, large_files
