"""Git-related utility functions."""

import logging
import os
import subprocess
from typing import List, Tuple

from gac.ai_utils import count_tokens
from gac.utils import run_subprocess

# Set up logger
logger = logging.getLogger(__name__)

# Constants for large file handling
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


def is_large_file(file_path: str) -> bool:
    """
    Check if a file should be treated as a large file based on its name and diff size.

    Args:
        file_path: Path to the file to check

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
        # Count tokens using the default model
        token_count = count_tokens(diff, "anthropic:claude-3-5-haiku-latest")
        return token_count > MAX_DIFF_TOKENS
    except Exception as e:
        logger.error(f"Error checking if {file_path} is large: {e}")
        return False


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

    for file in staged_files:
        try:
            file_diff = run_subprocess(["git", "--no-pager", "diff", "--staged", "--", file])
            if not file_diff:
                continue

            if is_large_file(file):
                # For large files, only include a summary
                truncated_files.append(file)
                diff_parts.append(f"# Large file {file} (truncated):")
                diff_parts.append(f"# File type: {os.path.splitext(file)[1]}")
                # Count tokens using the default model
                token_count = count_tokens(file_diff, "anthropic:claude-3-5-haiku-latest")
                diff_parts.append(f"# Changes: {token_count} tokens")
                diff_parts.append("...")
            else:
                diff_parts.append(file_diff)
        except Exception as e:
            logger.error(f"Error getting diff for {file}: {e}")
            # Even if there's an error, try to get a basic diff
            try:
                file_diff = run_subprocess(["git", "--no-pager", "diff", "--staged", "--", file])
                if file_diff:
                    diff_parts.append(file_diff)
            except Exception:
                continue

    return "\n".join(diff_parts), truncated_files


def get_staged_files() -> List[str]:
    """
    Get list of filenames of all staged files.

    M = Modified
    A = Added
    D = Deleted
    R = Renamed

    Returns:
        List of staged file paths
    """
    logger.debug("Checking staged files...")
    result = run_subprocess(["git", "status", "-s"])
    return [line.split()[1] for line in result.splitlines() if line[0] in "MADR"]


def get_staged_python_files() -> List[str]:
    """
    Get list of filenames of staged Python files.

    Returns:
        List of staged Python file paths
    """
    return [f for f in get_staged_files() if f.endswith(".py")]


def get_existing_staged_python_files() -> List[str]:
    """
    Get list of filenames of staged Python files that exist on disk.

    Returns:
        List of existing staged Python file paths
    """
    return [f for f in get_staged_python_files() if os.path.exists(f)]


def commit_changes(message: str) -> None:
    """
    Commit changes with the given message.

    Args:
        message: The commit message to use

    Raises:
        subprocess.CalledProcessError: If the git commit fails
        ValueError: If the commit message is empty
    """
    if not message:
        raise ValueError("Commit message cannot be empty")

    try:
        run_subprocess(["git", "commit", "-m", message])
    except subprocess.CalledProcessError as e:
        logger.error(f"Error committing changes: {e}")
        raise


def stage_files(files: List[str]) -> bool:
    """
    Stage files for commit.

    Args:
        files: List of files to stage (e.g., ["file1.py", "file2.py"])
               To stage all files, use ["*"]

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If no files are provided
    """
    if not files:
        raise ValueError("No files provided to stage")

    try:
        result = run_subprocess(["git", "add"] + files)
        logger.info("Files staged.")
        # Check if git add was successful by looking for error output
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
                # Handle different URL formats (HTTPS or SSH)
                if "github.com" in remote_url:
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
                # Check if it's the default description
                if (
                    file_content
                    != "Unnamed repository; edit this file 'description' to name the repository."  # noqa: E501 W503
                ):
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
