"""Git-related utility functions."""

import logging
import os
import re
import subprocess
from typing import List, Optional, Tuple

from gac.ai_utils import count_tokens
from gac.utils import run_subprocess

# Set up logger
logger = logging.getLogger(__name__)

# Constants for file handling
MAX_DIFF_TOKENS = 1000  # Maximum number of tokens to include for large files
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


def get_staged_files(file_type: Optional[str] = None, existing_only: bool = False) -> List[str]:
    """
    Get list of filenames of staged files with optional filtering.

    Args:
        file_type: Optional file extension to filter by (e.g., ".py")
        existing_only: If True, only return files that exist on disk

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

        if is_large_file(file_path, model):
            # For large files, apply smart truncation
            return smart_truncate_diff(file_diff, MAX_DIFF_TOKENS, model)
        else:
            return file_diff
    except Exception as e:
        logger.error(f"Error getting diff for {file_path}: {e}")
        return f"# Error processing {file_path}: {str(e)}"


def get_staged_diff(max_input_tokens: int = 4096) -> Tuple[str, List[str]]:
    """
    Get the staged diff, handling large files appropriately.

    Args:
        max_input_tokens: Maximum tokens to include in the full diff

    Returns:
        Tuple containing:
        - The full diff string
        - List of files that were truncated
    """
    staged_files = get_staged_files()
    truncated_files = []
    diff_parts = []
    model = "anthropic:claude-3-5-haiku-latest"

    # Get all file diffs and their info
    file_diffs = []
    total_tokens = 0

    for file in staged_files:
        file_diff = get_file_diff(file, model)
        if not file_diff:
            continue

        # Check if this file was truncated
        if "# Note: Diff has been truncated" in file_diff or "# Changes:" in file_diff:
            truncated_files.append(file)

        tokens = count_tokens(file_diff, model)
        priority = get_file_priority(file)

        file_diffs.append({"path": file, "diff": file_diff, "tokens": tokens, "priority": priority})

        total_tokens += tokens

    # If we're under the token limit, use all diffs
    if total_tokens <= max_input_tokens:
        for file_info in file_diffs:
            diff_parts.append(file_info["diff"])
    else:
        # Need to prioritize and fit within token budget
        # Sort by priority (highest first)
        file_diffs.sort(key=lambda x: x["priority"], reverse=True)

        # Budget for file diffs
        budget_used = 0
        budget_limit = max_input_tokens * 0.95  # Leave 5% for overhead

        for file_info in file_diffs:
            if budget_used + file_info["tokens"] <= budget_limit:
                # This file fits in our budget
                diff_parts.append(file_info["diff"])
                budget_used += file_info["tokens"]
            else:
                # Try to include a truncated version
                truncated_diff = smart_truncate_diff(
                    file_info["diff"],
                    int(max_input_tokens * 0.1),  # Allocate 10% of budget max
                    model,
                )
                truncated_tokens = count_tokens(truncated_diff, model)

                if budget_used + truncated_tokens <= budget_limit:
                    diff_parts.append(truncated_diff)
                    budget_used += truncated_tokens
                    truncated_files.append(file_info["path"])
                else:
                    # Can't include even a truncated version, create a minimal summary
                    summary = (
                        f"# File: {file_info['path']} (omitted)\n"
                        f"# Changes: approximately {file_info['tokens']} tokens\n"
                    )
                    summary_tokens = count_tokens(summary, model)

                    if budget_used + summary_tokens <= budget_limit:
                        diff_parts.append(summary)
                        budget_used += summary_tokens
                        truncated_files.append(file_info["path"])

        # Add note about truncation
        if len(staged_files) > len(diff_parts):
            note = (
                f"# Note: {len(staged_files) - len(diff_parts)} files were completely "
                f"omitted to stay within token limit.\n"
                f"# Total token budget: {max_input_tokens}, used approximately "
                f"{int(budget_used)}\n"
            )
            diff_parts.insert(0, note)

    return "\n".join(diff_parts), truncated_files


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


def get_project_description() -> str:
    """
    Get the Git project description and repo name if available.

    Returns:
        String containing repo name and description, or empty string if not available
    """
    try:
        # Get the git directory path
        git_dir = run_subprocess(["git", "rev-parse", "--git-dir"]).strip()

        # Try to get the repository name from remote URL
        repo_name = ""
        try:
            remote_url = run_subprocess(["git", "config", "--get", "remote.origin.url"]).strip()
            if remote_url:
                # Extract repo name from remote URL
                if remote_url.endswith(".git"):
                    remote_url = remote_url[:-4]  # Remove .git suffix
                repo_name = remote_url.split("/")[-1]
        except subprocess.CalledProcessError:
            # If we can't get the remote URL, try to get it from the directory name
            try:
                repo_dir = run_subprocess(["git", "rev-parse", "--show-toplevel"]).strip()
                repo_name = os.path.basename(repo_dir)
            except subprocess.CalledProcessError:
                pass

        # Check for a local description file
        description = ""
        description_file = os.path.join(git_dir, "description")
        if os.path.exists(description_file):
            with open(description_file, "r") as f:
                file_content = f.read().strip()
                # Check if it's not the default description
                default_msg = (
                    "Unnamed repository; edit this file 'description' to name the repository."
                )
                if file_content != default_msg:
                    description = file_content

        # Combine repo name and description
        result = []
        if repo_name:
            result.append(f"Repository: {repo_name}")
        if description:
            result.append(f"Description: {description}")

        return "\n".join(result)
    except Exception as e:
        logger.error(f"Error getting project description: {e}")
        return ""
