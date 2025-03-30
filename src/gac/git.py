"""Git-related utility functions."""

import logging
import os
import subprocess
from typing import List, Optional, Tuple

from gac.ai_utils import count_tokens
from gac.utils import run_subprocess

# Set up logger
logger = logging.getLogger(__name__)

# Constants for file handling
MAX_DIFF_TOKENS = 1000  # Maximum number of tokens to include for large files
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
]


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
            # For large files, only include a summary
            file_ext = os.path.splitext(file_path)[1]
            token_count = count_tokens(file_diff, model)
            return (
                f"# Large file {file_path} (truncated):\n"
                f"# File type: {file_ext}\n"
                f"# Changes: {token_count} tokens\n..."
            )
        else:
            return file_diff
    except Exception as e:
        logger.error(f"Error getting diff for {file_path}: {e}")
        return f"# Error processing {file_path}: {str(e)}"


def get_staged_diff() -> Tuple[str, List[str]]:
    """
    Get the staged diff, handling large files appropriately.

    Returns:
        Tuple containing:
        - The full diff string
        - List of files that were truncated
    """
    staged_files = get_staged_files()
    truncated_files = []
    diff_parts = []
    model = "anthropic:claude-3-5-haiku-latest"

    for file in staged_files:
        file_diff = get_file_diff(file, model)
        if not file_diff:
            continue

        # Check if this file was truncated (starts with the large file marker)
        if file_diff.startswith(f"# Large file {file}"):
            truncated_files.append(file)

        diff_parts.append(file_diff)

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

        return "; ".join(result)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        logger.debug("Failed to get project description, possibly not in a git repository")
        return ""
