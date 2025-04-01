"""Git-related utility functions for GAC."""

import logging
import os
import re
import subprocess
from enum import Enum, auto
from typing import Dict, List, Optional

from gac.ai import count_tokens

# Set up logger
logger = logging.getLogger(__name__)

# For backwards compatibility with tests
from enum import Enum, auto


class FileStatus(Enum):
    """File status for Git operations."""

    MODIFIED = auto()
    ADDED = auto()
    DELETED = auto()
    RENAMED = auto()
    COPIED = auto()
    UNTRACKED = auto()


# Global for test mock injection
_git_operations = None


def get_git_operations():
    """Get the current git operations implementation."""
    global _git_operations
    if _git_operations is None:
        _git_operations = RealGitOperations()
    return _git_operations


def set_git_operations(operations):
    """Set the git operations implementation."""
    global _git_operations
    _git_operations = operations


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


def get_project_description() -> str:
    """Get a description of the current git project.

    Returns:
        A string describing the repository
    """
    try:
        # Try to get the repository URL
        remote_url = run_git_command(["config", "--get", "remote.origin.url"], silent=True)
        if remote_url:
            # Extract repository name from URL
            repo_name = remote_url.split("/")[-1].split(".")[0]
            return f"Repository: {repo_name}"
        else:
            # Fallback to getting the directory name
            git_dir = ensure_git_directory()
            if git_dir:
                repo_name = os.path.basename(git_dir)
                return f"Repository: {repo_name}"

        return "Unknown repository"
    except Exception as e:
        logger.debug(f"Error getting project description: {e}")
        return "Unknown repository"


def is_test_mode() -> bool:
    """Check if we're running in test mode."""
    return os.environ.get("GAC_TEST_MODE", "").lower() == "true"


def is_large_file(file_path: str) -> bool:
    """
    Check if a file is considered large or auto-generated.

    Args:
        file_path: Path to the file

    Returns:
        True if the file is large or auto-generated
    """
    # First check if the file matches known large file patterns
    for pattern in LARGE_FILE_PATTERNS:
        if pattern.endswith("/*"):
            # Check directory pattern
            dir_pattern = pattern[:-2]
            if file_path.startswith(dir_pattern):
                return True
        elif pattern.startswith("*"):
            # Check extension pattern
            if file_path.endswith(pattern[1:]):
                return True
        elif pattern == file_path:
            # Exact match
            return True

    # If not a known pattern, check content size
    try:
        # Get the diff for the specific file
        diff = run_git_command(["diff", "--cached", "--", file_path])
        if not diff:
            return False

        # Count tokens in the diff
        token_count = count_tokens(diff, "test:model")

        # Consider large if token count exceeds threshold
        return token_count > MAX_DIFF_TOKENS
    except Exception as e:
        logger.debug(f"Error checking file size: {e}")
        return False


# Abstract class for test implementations
class GitOperations:
    """Abstract base class for Git operations."""

    def run_git_command(self, args: List[str], silent: bool = False) -> str:
        """Run a git command and return the output."""
        raise NotImplementedError

    def ensure_git_directory(self) -> Optional[str]:
        """Ensure we're in a git repository."""
        raise NotImplementedError

    def get_status(self) -> str:
        """Get git status."""
        raise NotImplementedError

    def get_staged_files(self, file_type: Optional[str] = None) -> List[str]:
        """Get list of staged files."""
        raise NotImplementedError

    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """Get the diff of staged changes."""
        raise NotImplementedError

    def stage_files(self, files: List[str]) -> bool:
        """Stage files for commit."""
        raise NotImplementedError

    def stage_all_files(self) -> bool:
        """Stage all files in the repository."""
        raise NotImplementedError

    def commit_changes(self, message: str) -> bool:
        """Commit staged changes with the given message."""
        raise NotImplementedError

    def push_changes(self) -> bool:
        """Push committed changes to the remote repository."""
        raise NotImplementedError

    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes."""
        raise NotImplementedError


class RealGitOperations(GitOperations):
    """Real implementation of Git operations."""

    def __init__(self, quiet: bool = False):
        """Initialize with quiet option."""
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


class TestGitOperations(GitOperations):
    """Test implementation of Git operations."""

    def __init__(
        self,
        mock_status=None,
        mock_staged_files=None,
        mock_staged_diff=None,
        mock_project_description=None,
    ):
        """Initialize with mocks for testing.

        Args:
            mock_status: Mock git status output
            mock_staged_files: Mock dictionary of staged files with status
            mock_staged_diff: Mock git diff output
            mock_project_description: Mock project description
        """
        self.status = mock_status or "On branch main\nNothing to commit, working tree clean"
        self.mock_staged_files = mock_staged_files or {}
        self.mock_staged_diff = (
            mock_staged_diff or "diff --git a/test.py b/test.py\n@@ -1,1 +1,1 @@\n-test\n+updated"
        )
        self.mock_project_description = mock_project_description or "Repository: test-repo"

        # For tracking calls
        self.calls = []
        self.commit_messages = []
        self.staged_file_lists = []

    def run_git_command(self, args: List[str], silent: bool = False) -> str:
        """Mock git command execution."""
        self.calls.append(("run_git_command", {"args": args, "silent": silent}))

        # Return mocks for specific commands
        if "status" in args:
            return self.status
        elif "diff" in args and "--cached" in args:
            return self.mock_staged_diff
        elif "rev-parse" in args and "--show-toplevel" in args:
            return "/mock/git/dir"
        elif args == ["config", "--get", "remote.origin.url"]:
            return "git@github.com:user/test-repo.git"

        return ""

    def ensure_git_directory(self) -> Optional[str]:
        """Mock git directory check."""
        self.calls.append(("ensure_git_directory", {}))
        return "/mock/git/dir"

    def get_status(self) -> str:
        """Get mock git status."""
        self.calls.append(("get_status", {}))
        return self.status

    def get_staged_files(
        self, file_type: Optional[str] = None, existing_only: bool = False
    ) -> List[str]:
        """Get mock staged files with optional filtering."""
        self.calls.append(
            ("get_staged_files", {"file_type": file_type, "existing_only": existing_only})
        )

        files = list(self.mock_staged_files.keys())

        # Apply filters if needed
        if file_type:
            files = [f for f in files if f.endswith(file_type)]

        return files

    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """Get mock staged diff."""
        self.calls.append(("get_staged_diff", {"file_path": file_path}))
        return self.mock_staged_diff

    def stage_files(self, files: List[str]) -> bool:
        """Mock stage files."""
        self.calls.append(("stage_files", {"files": files}))
        self.staged_file_lists.append(files)
        return True

    def stage_all_files(self) -> bool:
        """Mock stage all files."""
        self.calls.append(("stage_all_files", {}))
        return True

    def commit_changes(self, message: str) -> bool:
        """Mock commit changes."""
        self.calls.append(("commit_changes", {"message": message}))
        self.commit_messages.append(message)
        return True

    def push_changes(self) -> bool:
        """Mock push changes."""
        self.calls.append(("push_changes", {}))
        return True

    def has_staged_changes(self) -> bool:
        """Check if mock has staged changes."""
        self.calls.append(("has_staged_changes", {}))
        return bool(self.mock_staged_files)

    def _get_file_diff(self, file_path: str) -> str:
        """Mock getting diff for a specific file."""
        self.calls.append(("_get_file_diff", {"file_path": file_path}))
        return f"diff --git a/{file_path} b/{file_path}\n+New line"

    def get_project_description(self) -> str:
        """Get mock project description."""
        self.calls.append(("get_project_description", {}))
        return self.mock_project_description


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
