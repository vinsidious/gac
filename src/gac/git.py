"""Git-related utility functions."""

import logging
import os
import re
import subprocess
from typing import List, Optional, Tuple

from gac.ai_utils import count_tokens
from gac.cache import Cache, cached
from gac.utils import run_subprocess

# Set up logger
logger = logging.getLogger(__name__)

# Constants for file handling
MAX_DIFF_TOKENS = 2500  # Maximum number of tokens to include for large files
# Files that are usually auto-generated or less important for commit context
LARGE_FILE_PATTERNS = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "mix.lock",
    "*.lock",
    "node_modules/*",
    "dist/*",
    "build/*",
]

# Cache expiration times (in seconds)
GIT_CACHE_EXPIRATION = 5 * 60  # 5 minutes for most git operations
DIFF_CACHE_EXPIRATION = 60  # 1 minute for diff operations (more volatile)

# Create cache instances
git_cache = Cache(expiration=GIT_CACHE_EXPIRATION)
diff_cache = Cache(expiration=DIFF_CACHE_EXPIRATION)

# Priorities for different file types (higher = more important)
FILE_PRIORITY = {
    ".md": 5,  # Documentation
    ".rst": 5,  # Documentation
    ".txt": 4,  # Text files
    ".py": 5,  # Python code
    ".js": 5,  # JavaScript code
    ".ts": 5,  # TypeScript code
    ".jsx": 5,  # React JSX
    ".tsx": 5,  # React TSX
    ".java": 4,  # Java code
    ".go": 4,  # Go code
    ".rs": 4,  # Rust code
    ".c": 4,  # C code
    ".cpp": 4,  # C++ code
    ".h": 4,  # C/C++ header
    ".html": 3,  # HTML
    ".css": 3,  # CSS
    ".scss": 3,  # SCSS
    ".json": 2,  # JSON config
    ".yaml": 2,  # YAML config
    ".yml": 2,  # YAML config
    ".toml": 2,  # TOML config
    ".lock": 1,  # Lock files
}


class FileStatus:
    """Constants for file status in git."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"

    @classmethod
    def is_valid_status(cls, status: str) -> bool:
        """Check if a status code is valid."""
        return status in [cls.MODIFIED, cls.ADDED, cls.DELETED, cls.RENAMED]


def is_large_file(file_path: str, model: str = "anthropic:claude-3-5-haiku-latest") -> bool:
    """
    Check if a file should be treated as a large file based on its name and diff size.

    Args:
        file_path: Path to the file to check
        model: Model to use for token counting

    Returns:
        bool: True if the file should be treated as large
    """
    # Check if file matches any of the large file patterns
    if any(pattern in file_path for pattern in LARGE_FILE_PATTERNS):
        return True

    # Get the diff size for this file
    try:
        diff = run_subprocess(["git", "--no-pager", "diff", "--staged", "--", file_path])
        if not diff:
            return False
        # Count tokens using the specified model
        token_count = count_tokens(diff, model)
        return token_count > MAX_DIFF_TOKENS
    except Exception as e:
        logger.error(f"Error checking if {file_path} is large: {e}")
        return False


def get_file_priority(file_path: str) -> int:
    """
    Get priority score for a file based on its extension and content.

    Args:
        file_path: Path to the file

    Returns:
        Priority score (higher = more important)
    """
    # Get file extension
    _, ext = os.path.splitext(file_path)

    # Base priority on file extension
    priority = FILE_PRIORITY.get(ext.lower(), 3)  # Default priority is 3

    # Special case for important files
    if os.path.basename(file_path).lower() in [
        "readme.md",
        "changelog.md",
        "contributing.md",
        "license",
        "license.txt",
        "license.md",
        "pyproject.toml",
        "setup.py",
        "package.json",
        "cargo.toml",
        "makefile",
        "dockerfile",
    ]:
        priority += 2

    return priority


@cached(cache_instance=git_cache)
def get_staged_files(
    file_type: Optional[str] = None, existing_only: bool = False, cache_skip: bool = False
) -> List[str]:
    """
    Get list of filenames of staged files with optional filtering.

    Args:
        file_type: Optional file extension to filter by (e.g., ".py")
        existing_only: If True, only return files that exist on disk
        cache_skip: If True, bypass cache and force a new call

    Returns:
        List of staged file paths
    """
    logger.debug("Checking staged files...")
    result = run_subprocess(["git", "status", "-s"])

    # Get all staged files
    files = [line.split()[1] for line in result.splitlines() if line and line[0] in "MADR"]

    # Apply filters if needed
    if file_type:
        files = [f for f in files if f.endswith(file_type)]

    if existing_only:
        files = [f for f in files if os.path.exists(f)]

    return files


def smart_truncate_diff(diff: str, max_tokens: int, model: str) -> str:
    """
    Intelligently truncate a diff to fit within max_tokens while preserving context.

    Args:
        diff: The diff content
        max_tokens: Maximum tokens to keep
        model: Model to use for token counting

    Returns:
        Truncated diff maintaining important context
    """
    # If diff is already within token limit, return as is
    token_count = count_tokens(diff, model)
    if token_count <= max_tokens:
        return diff

    # Split by file chunks (each file diff starts with "diff --git")
    file_chunks = re.split(r"(diff --git )", diff)

    # Rejoin the split markers with their content
    if file_chunks[0] == "":
        file_chunks.pop(0)

    diff_chunks = []
    for i in range(0, len(file_chunks), 2):
        if i + 1 < len(file_chunks):
            diff_chunks.append(file_chunks[i] + file_chunks[i + 1])
        else:
            diff_chunks.append(file_chunks[i])

    # For each chunk, extract header and sample of changes
    processed_chunks = []

    for chunk in diff_chunks:
        # Extract chunk sections (header, hunks)
        lines = chunk.split("\n")

        # Find where the header ends and the hunks begin
        hunk_start_indices = [i for i, line in enumerate(lines) if line.startswith("@@")]

        if not hunk_start_indices:
            # No hunks found, keep the chunk as is
            processed_chunks.append(chunk)
            continue

        # Keep the header
        header = "\n".join(lines[: hunk_start_indices[0]])

        # For the hunks, keep the first few lines and last few lines of each
        processed_hunks = []

        for i in range(len(hunk_start_indices)):
            start = hunk_start_indices[i]
            end = hunk_start_indices[i + 1] if i + 1 < len(hunk_start_indices) else len(lines)

            hunk = lines[start:end]
            hunk_header = hunk[0]  # The @@ line

            if len(hunk) <= 10:
                # Small hunk, keep it all
                processed_hunks.append("\n".join(hunk))
            else:
                # Large hunk, keep header, first 4 lines, and last 3 lines
                context = "\n".join(
                    [
                        hunk_header,
                        *hunk[1:5],  # First 4 lines after header
                        "...",  # Indicator that content was omitted
                        *hunk[-3:],  # Last 3 lines
                    ]
                )
                processed_hunks.append(context)

        # Combine processed header and hunks
        processed_chunk = header + "\n" + "\n".join(processed_hunks)
        processed_chunks.append(processed_chunk)

    # Combine processed chunks and check if we're under the token limit
    result = "\n".join(processed_chunks)
    result_tokens = count_tokens(result, model)

    # If still over limit, we need to prioritize files
    if result_tokens > max_tokens:
        return prioritize_and_truncate_diffs(diff_chunks, max_tokens, model)

    return result


def prioritize_and_truncate_diffs(diff_chunks: List[str], max_tokens: int, model: str) -> str:
    """
    Prioritize diffs by file importance and truncate to fit token budget.

    Args:
        diff_chunks: List of file diff chunks
        max_tokens: Maximum tokens to use
        model: Model for token counting

    Returns:
        Prioritized and truncated diff
    """
    # Extract file paths and calculate priorities
    chunk_info = []

    for chunk in diff_chunks:
        match = re.search(r"diff --git a/(.*?) b/", chunk)
        path = match.group(1) if match else "unknown_file"
        priority = get_file_priority(path)
        tokens = count_tokens(chunk, model)

        chunk_info.append({"path": path, "priority": priority, "tokens": tokens, "content": chunk})

    # Sort by priority (highest first)
    chunk_info.sort(key=lambda x: x["priority"], reverse=True)

    # Build result within token budget
    result_chunks = []
    tokens_used = 0

    # Header to explain truncation
    header = (
        f"# Note: Diff has been truncated and prioritized to fit token limit of {max_tokens}\n\n"
    )
    header_tokens = count_tokens(header, model)
    tokens_used += header_tokens

    for info in chunk_info:
        # If adding this chunk would exceed budget, summarize it instead
        if tokens_used + info["tokens"] > max_tokens:
            # Create a summary instead
            summary = (
                f"# File: {info['path']} (truncated)\n"
                f"# Priority: {info['priority']}\n"
                f"# Changes: approximately {info['tokens']} tokens\n"
            )
            summary_tokens = count_tokens(summary, model)

            # If even the summary won't fit, we're done
            if tokens_used + summary_tokens > max_tokens:
                break

            result_chunks.append(summary)
            tokens_used += summary_tokens
        else:
            # Full chunk fits within budget
            result_chunks.append(info["content"])
            tokens_used += info["tokens"]

    return header + "\n".join(result_chunks)


def get_file_diff(file_path: str, model: str = "anthropic:claude-3-5-haiku-latest") -> str:
    """
    Get the diff for a single file, with appropriate handling for large files.

    Args:
        file_path: Path to the file to get diff for
        model: Model to use for token counting

    Returns:
        The diff string for the file, potentially truncated if it's large
    """
    try:
        file_diff = run_subprocess(["git", "--no-pager", "diff", "--staged", "--", file_path])
        if not file_diff:
            return ""

        token_count = count_tokens(file_diff, model)
        is_large = is_large_file(file_path, model) or token_count > MAX_DIFF_TOKENS

        if is_large:
            # For large files, apply smart truncation
            truncated_diff = smart_truncate_diff(file_diff, MAX_DIFF_TOKENS, model)
            truncation_msg = f"Large file {file_path} ({token_count} tokens, "
            truncation_msg += f"truncated to ~{MAX_DIFF_TOKENS} tokens):"
            return f"{truncation_msg}\n{truncated_diff}"
        else:
            return file_diff
    except Exception as e:
        logger.error(f"Error getting diff for {file_path}: {e}")
        return f"# Error processing {file_path}: {str(e)}"


@cached(cache_instance=diff_cache)
def get_staged_diff(
    file_path: Optional[str] = None,
    max_tokens: int = 16000,
    model: str = "anthropic:claude-3-5-haiku-latest",
    cache_skip: bool = False,
) -> Tuple[str, List[str]]:
    """
    Get the diff of staged changes, optionally for a specific file.

    Args:
        file_path: Optional specific file to get diff for
        max_tokens: Maximum tokens to include in the diff
        model: Model to use for token counting
        cache_skip: If True, bypass cache and force a new call

    Returns:
        A tuple containing:
        - The diff as a string
        - A list of files that were truncated due to size, with token counts
    """
    logger.debug(f"Getting staged diff{'for ' + file_path if file_path else ''}")

    # If a specific file is requested, handle it directly
    if file_path:
        command = ["git", "--no-pager", "diff", "--staged", "--", file_path]
        diff = run_subprocess(command)
        token_count = count_tokens(diff, model)

        if token_count > max_tokens:
            logger.info(
                f"Diff too large ({token_count} tokens), truncating to ~{max_tokens} tokens"
            )
            truncated_diff = smart_truncate_diff(diff, max_tokens, model)
            return truncated_diff, [f"{file_path} [{token_count} tokens]"]

        return diff, []

    # Handle all staged files
    staged_files = get_staged_files()
    if not staged_files:
        return "", []

    truncated_files = []
    truncated_files_with_counts = []
    combined_diff = []
    file_token_counts = {}

    # Process each file individually to track which ones are truncated
    for f in staged_files:
        # Get raw diff to calculate token count before any truncation
        raw_diff = run_subprocess(["git", "--no-pager", "diff", "--staged", "--", f])
        if raw_diff:
            file_token_count = count_tokens(raw_diff, model)
            file_token_counts[f] = file_token_count

        file_diff = get_file_diff(f, model)
        if "Large file" in file_diff and "(truncated)" in file_diff:
            truncated_files.append(f)
            # Add token count to the truncated file information
            truncated_files_with_counts.append(f"{f} [{file_token_counts.get(f, 0)} tokens]")
        if file_diff:
            combined_diff.append(file_diff)

    full_diff = "\n".join(combined_diff)

    # Final check if the combined diff is still too large
    token_count = count_tokens(full_diff, model)
    if token_count > max_tokens:
        logger.info(
            f"Combined diff too large ({token_count} tokens), truncating to ~{max_tokens} tokens"
        )
        truncated_diff = smart_truncate_diff(full_diff, max_tokens, model)

        # Since we're further truncating, all staged files are technically affected
        if not truncated_files_with_counts:
            # If no individual files were truncated earlier, add all with their token counts
            truncated_files_with_counts = [
                f"{f} [{file_token_counts.get(f, 0)} tokens]" for f in staged_files
            ]
            truncated_files = staged_files

        return truncated_diff, truncated_files_with_counts

    return full_diff, truncated_files_with_counts


def commit_changes(message: str) -> bool:
    """
    Commit changes with the given message.

    Args:
        message: The commit message to use

    Returns:
        True if commit successful, False otherwise
    """
    if not message:
        logger.error("Commit message cannot be empty")
        return False

    try:
        run_subprocess(["git", "commit", "-m", message])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error committing changes: {e}")
        return False


def stage_files(files: List[str]) -> bool:
    """
    Stage files for commit.

    Args:
        files: List of files to stage (e.g., ["file1.py", "file2.py"])
               To stage all files, use ["."]

    Returns:
        True if successful, False otherwise
    """
    if not files:
        logger.error("No files provided to stage")
        return False

    try:
        result = run_subprocess(["git", "add"] + files)
        logger.info("Files staged.")
        return "fatal" not in result.lower()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error staging files: {e}")
        return False


@cached(cache_instance=git_cache)
def get_project_description(cache_skip: bool = False) -> str:
    """
    Try to get a project description from common files and include repository name.

    Args:
        cache_skip: If True, bypass cache and force a new call

    Returns:
        A string description including repository name if available, or empty string if not found
    """
    description = ""
    repo_name = ""

    # Try to get the repository name from git remote URL
    try:
        # Get the git directory
        git_dir = run_subprocess(["git", "rev-parse", "--git-dir"], silent=True)
        if git_dir:
            # Get the remote URL
            remote_url = run_subprocess(
                ["git", "config", "--get", "remote.origin.url"], silent=True
            )
            if remote_url:
                # Extract repo name from URL (e.g., https://github.com/user/repo.git -> repo)
                parts = remote_url.rstrip("/").split("/")
                if parts:
                    repo_name = parts[-1].replace(".git", "")
    except Exception as e:
        logger.debug(f"Error getting repository name: {e}")

    # Check common locations for project descriptions
    description_files = [
        "README.md",
        "README.rst",
        "README",
        "README.txt",
        "DESCRIPTION",
        "package.json",
        "pyproject.toml",
    ]

    for file_path in description_files:
        if os.path.exists(file_path):
            logger.debug(f"Found potential description file: {file_path}")
            try:
                if file_path.endswith(("md", "rst", "txt")):
                    # For text files, just read the first few lines
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f.readlines()[:10] if line.strip()]
                        if lines:
                            # First non-empty line, usually the title
                            description = lines[0]
                            break

                elif file_path == "package.json":
                    # For package.json, extract the name and description
                    import json

                    with open(file_path, "r", encoding="utf-8") as f:
                        package_info = json.load(f)
                        if "description" in package_info:
                            description = package_info["description"]
                            break
                        elif "name" in package_info:
                            description = package_info["name"]
                            break

                elif file_path == "pyproject.toml":
                    # For pyproject.toml, extract the project description
                    import tomli

                    with open(file_path, "rb") as f:
                        pyproject = tomli.load(f)
                        if "project" in pyproject and "description" in pyproject["project"]:
                            description = pyproject["project"]["description"]
                            break
                        elif "tool" in pyproject and "poetry" in pyproject["tool"]:
                            poetry = pyproject["tool"]["poetry"]
                            if "description" in poetry:
                                description = poetry["description"]
                                break

            except Exception as e:
                logger.debug(f"Error reading {file_path}: {e}")

    # Combine repository name and description if available
    if repo_name and description:
        return f"Repository: {repo_name}; Description: {description}"
    elif repo_name:
        return f"Repository: {repo_name}"
    elif description:
        return description
    else:
        return ""


@cached(cache_instance=git_cache)
def get_status(cache_skip: bool = False) -> str:
    """
    Get the current git status.

    Args:
        cache_skip: If True, bypass cache and force a new call

    Returns:
        String containing git status output
    """
    try:
        logger.debug("Getting git status...")
        return run_subprocess(["git", "status", "--porcelain", "--branch"])
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git status: {e}")
        return "Error getting git status"
