"""Git-related utility functions for GAC."""

import logging
import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple

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
    "*.lock",
    "node_modules/*",
    "dist/*",
    "build/*",
]


def run_git_command(args: List[str], silent: bool = False, timeout: int = 30) -> str:
    """
    Run a git command and return the output.

    Args:
        args: List of arguments to pass to git
        silent: If True, suppress debug logging
        timeout: Command timeout in seconds

    Returns:
        Command output as string, or empty string on error
    """
    if not silent:
        logger.debug(f"Running git command: git {' '.join(args)}")

    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if not silent:
            logger.error(f"Git command failed: {e.stderr.strip()}")
        return ""
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out: git {' '.join(args)}")
        return ""


def ensure_git_directory() -> Optional[str]:
    """
    Ensure we're in a git repository and change to the root directory if needed.

    Returns:
        The git repository root directory or None if not a git repository
    """
    try:
        # Try to get the git root directory
        git_dir = run_git_command(["rev-parse", "--show-toplevel"])
        if not git_dir:
            logger.error("Not in a git repository")
            return None

        # Change to the git repository root if we're not already there
        current_dir = os.getcwd()
        if git_dir and git_dir != current_dir:
            logger.debug(f"Changing directory to git root: {git_dir}")
            os.chdir(git_dir)

        return git_dir
    except Exception as e:
        logger.error(f"Error determining git directory: {e}")
        return None


def get_status() -> str:
    """
    Get git status.

    Returns:
        Git status output as string
    """
    return run_git_command(["status"])


def get_staged_files(file_type: Optional[str] = None, existing_only: bool = False) -> List[str]:
    """
    Get list of staged files with optional filtering.

    Args:
        file_type: Optional file extension to filter by (e.g., ".py")
        existing_only: If True, only return files that exist on disk

    Returns:
        List of staged file paths
    """
    # Get list of staged files
    output = run_git_command(["diff", "--name-only", "--cached"])
    if not output:
        return []

    # Parse the output to get files
    files = [line.strip() for line in output.splitlines() if line.strip()]

    # Apply filters if needed
    if file_type:
        files = [f for f in files if f.endswith(file_type)]

    if existing_only:
        files = [f for f in files if os.path.exists(f)]

    return files


def get_staged_files_with_status() -> Dict[str, str]:
    """
    Get staged files with their status (M, A, D, R, etc.).

    Returns:
        Dictionary mapping file paths to their status
    """
    result = run_git_command(["status", "-s"])
    if not result:
        return {}

    # Parse the output to get files and their statuses
    file_statuses = {}
    for line in result.splitlines():
        if not line or len(line) < 2:
            continue

        status = line[0]
        if status.strip() and line[1] == " ":  # Staged changes
            file_path = line[3:].strip()
            file_statuses[file_path] = status

    return file_statuses


def get_staged_diff(file_path: Optional[str] = None) -> str:
    """
    Get the diff of staged changes, optionally for a specific file.

    Args:
        file_path: Optional specific file to get diff for

    Returns:
        The diff as a string
    """
    args = ["diff", "--cached"]
    if file_path:
        args.extend(["--", file_path])

    return run_git_command(args)


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
        # Stage each file individually to get better error handling
        for file in files:
            result = run_git_command(["add", file], silent=True)
            if result and "fatal:" in result.lower():
                logger.error(f"Failed to stage {file}")
                return False

        logger.info(f"Staged {len(files)} files")
        return True
    except Exception as e:
        logger.error(f"Error staging files: {e}")
        return False


def stage_all_files() -> bool:
    """
    Stage all files in the repository.

    Returns:
        True if successful, False otherwise
    """
    # Check if this is an empty repository
    status = get_status()
    is_empty_repo = "No commits yet" in status

    if is_empty_repo:
        logger.info("Repository has no commits yet. Creating initial commit...")

        # Try to stage files in the empty repo
        if not stage_files(["."]):
            # Try with an empty commit as fallback
            run_git_command(["commit", "--allow-empty", "-m", "Initial commit"])
            # Now try to stage files again
            return stage_files(["."])

    # Normal case - just stage all files
    return stage_files(["."])


def commit_changes(message: str) -> bool:
    """
    Commit staged changes with the given message.

    Args:
        message: The commit message to use

    Returns:
        True if commit successful, False otherwise
    """
    if not message:
        logger.error("Commit message cannot be empty")
        return False

    result = run_git_command(["commit", "-m", message])
    return bool(result)


def push_changes() -> bool:
    """
    Push committed changes to the remote repository.

    Returns:
        True if successful, False otherwise
    """
    logger.info("Pushing changes to remote...")
    result = run_git_command(["push"])
    return bool(result)


def has_staged_changes() -> bool:
    """
    Check if there are any staged changes.

    Returns:
        True if there are staged changes, False otherwise
    """
    return bool(get_staged_files())


def is_large_file(file_path: str) -> bool:
    """
    Check if a file is likely to be large or auto-generated.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file matches patterns for large/generated files
    """
    # Check against patterns
    for pattern in LARGE_FILE_PATTERNS:
        if pattern.endswith("/*"):
            # Directory pattern
            dir_pattern = pattern[:-2]
            if file_path.startswith(dir_pattern):
                return True
        elif "*" in pattern:
            # Simple glob pattern
            escaped = re.escape(pattern).replace("\\*", ".*")
            if re.match(escaped, file_path):
                return True
        else:
            # Exact match
            if file_path.endswith(pattern):
                return True

    return False


def get_project_description() -> str:
    """
    Generate a brief description of the git project.

    Returns:
        A string describing the project
    """
    description = []

    # Try to get repository name
    try:
        # Get the remote URL
        remote_url = run_git_command(["remote", "get-url", "origin"], silent=True)
        if remote_url:
            # Extract repository name from URL
            repo_name = remote_url.split("/")[-1].replace(".git", "")
            description.append(f"Repository: {repo_name}")
    except Exception:
        pass

    # Current branch
    try:
        branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], silent=True)
        if branch:
            description.append(f"Branch: {branch}")
    except Exception:
        pass

    # Try to get root directory name
    try:
        root_dir = run_git_command(["rev-parse", "--show-toplevel"], silent=True)
        if root_dir:
            dir_name = os.path.basename(root_dir)
            description.append(f"Directory: {dir_name}")
    except Exception:
        pass

    # Try to get the commit count
    try:
        commit_count = run_git_command(["rev-list", "--count", "HEAD"], silent=True)
        if commit_count and commit_count.isdigit():
            description.append(f"Commits: {commit_count}")
    except Exception:
        pass

    # Try to identify the project language from file types
    try:
        # Get all files
        all_files = run_git_command(["ls-files"], silent=True).splitlines()

        # Count file extensions
        extensions = {}
        for file in all_files:
            ext = os.path.splitext(file)[1].lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

        # Get the most common extension
        if extensions:
            most_common = max(extensions.items(), key=lambda x: x[1])
            if most_common[0] == ".py":
                description.append("Language: Python")
            elif most_common[0] in [".js", ".ts", ".jsx", ".tsx"]:
                description.append("Language: JavaScript/TypeScript")
            elif most_common[0] in [".java", ".kt"]:
                description.append("Language: Java/Kotlin")
            elif most_common[0] in [".c", ".cpp", ".h", ".hpp"]:
                description.append("Language: C/C++")
            elif most_common[0] == ".go":
                description.append("Language: Go")
            elif most_common[0] == ".rs":
                description.append("Language: Rust")
            elif most_common[0] in [".rb", ".rake"]:
                description.append("Language: Ruby")
            elif most_common[0] == ".php":
                description.append("Language: PHP")
            elif most_common[0] == ".cs":
                description.append("Language: C#")
    except Exception:
        pass

    return ", ".join(description) if description else "Git repository"


def is_test_mode() -> bool:
    """Check if we're running in test mode."""
    return os.environ.get("GAC_TEST_MODE", "").lower() == "true"


# For compatibility with existing code that might use the class-based interface
class GitOperationsManager:
    """GitOperationsManager provides Git operations."""

    def __init__(self, quiet: bool = False):
        """
        Initialize the GitOperationsManager.

        Args:
            quiet: Whether to suppress logging
        """
        self.quiet = quiet

    def run_git_command(self, args: List[str], silent: bool = False) -> str:
        """Run a git command and return the output."""
        return run_git_command(args, silent or self.quiet)

    def ensure_git_directory(self) -> Optional[str]:
        """Ensure we're in a git repository."""
        return ensure_git_directory()

    def get_status(self) -> str:
        """Get git status."""
        return get_status()

    def get_staged_files(self, file_type: Optional[str] = None) -> List[str]:
        """Get list of staged files."""
        return get_staged_files(file_type)

    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """Get the diff of staged changes."""
        return get_staged_diff(file_path)

    def stage_files(self, files: List[str]) -> bool:
        """Stage files for commit."""
        return stage_files(files)

    def stage_all_files(self) -> bool:
        """Stage all files in the repository."""
        return stage_all_files()

    def commit_changes(self, message: str) -> bool:
        """Commit staged changes with the given message."""
        return commit_changes(message)

    def push_changes(self) -> bool:
        """Push committed changes to the remote repository."""
        return push_changes()

    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes."""
        return has_staged_changes()
