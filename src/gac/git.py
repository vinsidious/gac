"""Git-related utility functions."""

import abc
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional

from gac.ai_utils import count_tokens
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
    COPIED = "C"
    TYPE_CHANGED = "T"

    @classmethod
    def is_valid_status(cls, status: str) -> bool:
        """Check if a status code is valid."""
        if not status:
            return False
        first_char = status[0]
        return first_char in [
            cls.MODIFIED,
            cls.ADDED,
            cls.DELETED,
            cls.RENAMED,
            cls.COPIED,
            cls.TYPE_CHANGED,
        ]


class GitOperations(abc.ABC):
    """Abstract base class for git operations."""

    @abc.abstractmethod
    def get_status(self) -> str:
        """Get the current git status."""
        pass

    @abc.abstractmethod
    def get_staged_files(
        self, file_type: Optional[str] = None, existing_only: bool = False
    ) -> Dict[str, str]:
        """Get list of staged files with optional filtering."""
        pass

    @abc.abstractmethod
    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """Get the diff of staged changes, optionally for a specific file."""
        pass

    @abc.abstractmethod
    def commit_changes(self, message: str) -> bool:
        """Commit changes with the given message."""
        pass

    @abc.abstractmethod
    def stage_files(self, files: List[str]) -> bool:
        """Stage files for commit."""
        pass

    @abc.abstractmethod
    def get_project_description(self) -> str:
        """Try to get a project description from common files and include repository name."""
        pass


class RealGitOperations(GitOperations):
    """Implementation of GitOperations that interacts with a real git repository."""

    def get_status(self) -> str:
        """Get the current git status."""
        try:
            output = run_subprocess(["git", "status"], silent=True, timeout=10)
            return output
        except subprocess.CalledProcessError:
            logger.error("Failed to get git status. Are you in a git repository?")
            return ""

    def get_staged_files(
        self, file_type: Optional[str] = None, existing_only: bool = False
    ) -> Dict[str, str]:
        """
        Get list of staged files with optional filtering.

        Args:
            file_type: Optional file extension to filter by (e.g., ".py")
            existing_only: If True, only return files that exist on disk

        Returns:
            Dictionary mapping file paths to their status (M, A, D, R)
        """
        logger.debug("Checking staged files...")
        result = run_subprocess(["git", "status", "-s"])

        # Parse the output to get files and their statuses
        file_statuses = {}
        for line in result.splitlines():
            if not line or line[0] not in "MADR":
                continue

            status = line[0]
            file_path = line.split(maxsplit=1)[1]

            # Apply filters if needed
            if file_type and not file_path.endswith(file_type):
                continue

            if existing_only and not os.path.exists(file_path):
                continue

            file_statuses[file_path] = status

        return file_statuses

    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """
        Get the diff of staged changes, optionally for a specific file.

        Args:
            file_path: Optional specific file to get diff for

        Returns:
            The diff as a string
        """
        logger.debug(f"Getting staged diff{'for ' + file_path if file_path else ''}")

        # If a specific file is requested, handle it directly
        if file_path:
            command = ["git", "--no-pager", "diff", "--staged", "--", file_path]
            return run_subprocess(command)

        # Handle all staged files
        staged_files = self.get_staged_files()
        if not staged_files:
            return ""

        combined_diff = []

        # Process each file individually
        for f in staged_files:
            file_diff = self._get_file_diff(f)
            if file_diff:
                combined_diff.append(file_diff)

        return "\n".join(combined_diff)

    def _get_file_diff(
        self, file_path: str, model: str = "anthropic:claude-3-5-haiku-latest"
    ) -> str:
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
            is_large = self._is_large_file(file_path, model) or token_count > MAX_DIFF_TOKENS

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

    def _is_large_file(
        self, file_path: str, model: str = "anthropic:claude-3-5-haiku-latest"
    ) -> bool:
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

    def commit_changes(self, message: str) -> bool:
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

    def stage_files(self, files: List[str]) -> bool:
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
            # Check for specific error: no commit checked out
            error_str = str(e.stderr) if hasattr(e, "stderr") else str(e)
            if "does not have a commit checked out" in error_str:
                logger.warning("Repository has no initial commit. Creating an initial commit...")
                try:
                    # Create an initial empty commit
                    run_subprocess(["git", "commit", "--allow-empty", "-m", "Initial commit"])
                    # Now try to stage files again
                    result = run_subprocess(["git", "add"] + files)
                    logger.info("Files staged after creating initial commit.")
                    return True
                except subprocess.CalledProcessError as inner_e:
                    logger.error(f"Error creating initial commit: {inner_e}")
                    return False
            else:
                logger.error(f"Error staging files: {e}")
                return False

    def get_project_description(self) -> str:
        """
        Try to get a project description from common files and include repository name.

        Returns:
            A string description including repository name if available,
            or empty string if not found
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


class TestGitOperations(GitOperations):
    """Mock implementation of GitOperations for testing."""

    def __init__(
        self,
        mock_status: str = "",
        mock_staged_files: Dict[str, str] = None,
        mock_staged_diff: str = "",
        mock_project_description: str = "",
    ):
        """
        Initialize with mock responses.

        Args:
            mock_status: Mock git status output
            mock_staged_files: Mock staged files mapping paths to statuses
            mock_staged_diff: Mock git diff output
            mock_project_description: Mock project description
        """
        self.mock_status = (
            mock_status or "On branch main\nChanges to be committed:\n  modified: file1.py"
        )
        self.mock_staged_files = mock_staged_files or {"file1.py": "M"}
        self.mock_staged_diff = (
            mock_staged_diff or "diff --git a/file1.py b/file1.py\n+Test content"
        )
        self.mock_project_description = mock_project_description or "Repository: test-repo"

        # Track calls for verification in tests
        self.calls = []
        self.commit_messages = []
        self.staged_file_lists = []

    def get_status(self) -> str:
        """Get mock git status."""
        self.calls.append(("get_status", {}))
        return self.mock_status

    def get_staged_files(
        self, file_type: Optional[str] = None, existing_only: bool = False
    ) -> Dict[str, str]:
        """Get mock staged files."""
        self.calls.append(
            ("get_staged_files", {"file_type": file_type, "existing_only": existing_only})
        )

        # Apply filters if needed
        result = {}
        for file_path, status in self.mock_staged_files.items():
            if file_type and not file_path.endswith(file_type):
                continue
            result[file_path] = status

        return result

    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """Get mock git diff."""
        self.calls.append(("get_staged_diff", {"file_path": file_path}))
        return self.mock_staged_diff

    def commit_changes(self, message: str) -> bool:
        """Record commit message and return success."""
        self.calls.append(("commit_changes", {"message": message}))
        self.commit_messages.append(message)
        return True

    def stage_files(self, files: List[str]) -> bool:
        """Record staged files and return success."""
        self.calls.append(("stage_files", {"files": files}))
        self.staged_file_lists.append(files)
        return True

    def get_project_description(self) -> str:
        """Get mock project description."""
        self.calls.append(("get_project_description", {}))
        return self.mock_project_description

    def reset_calls(self):
        """Reset tracked calls for a fresh test."""
        self.calls = []
        self.commit_messages = []
        self.staged_file_lists = []


# Global git operations instance
_git_operations = RealGitOperations()


def set_git_operations(operations: GitOperations):
    """
    Set the git operations implementation.

    This allows for dependency injection, particularly useful for testing.

    Args:
        operations: The GitOperations implementation to use
    """
    global _git_operations
    _git_operations = operations


def get_git_operations() -> GitOperations:
    """
    Get the current git operations implementation.

    Returns:
        The current GitOperations instance
    """
    return _git_operations


# Functions that delegate to the current GitOperations implementation
def get_status() -> str:
    """Get the current git status."""
    return _git_operations.get_status()


def get_staged_files(file_type: Optional[str] = None, existing_only: bool = False) -> List[str]:
    """
    Get list of filenames of staged files with optional filtering.

    Args:
        file_type: Optional file extension to filter by (e.g., ".py")
        existing_only: If True, only return files that exist on disk

    Returns:
        List of staged file paths
    """
    return list(_git_operations.get_staged_files(file_type, existing_only).keys())


def get_staged_diff(
    file_path: Optional[str] = None,
    max_tokens: int = 16000,
    model: str = "anthropic:claude-3-5-haiku-latest",
) -> str:
    """
    Get the diff of staged changes, optionally for a specific file.

    Args:
        file_path: Optional specific file to get diff for
        max_tokens: Maximum tokens to include in the diff
        model: Model to use for token counting

    Returns:
        The diff as a string
    """
    diff = _git_operations.get_staged_diff(file_path)

    # Check if truncation is needed based on token count
    token_count = count_tokens(diff, model)
    if token_count > max_tokens:
        logger.info(f"Diff too large ({token_count} tokens), truncating to ~{max_tokens} tokens")
        return smart_truncate_diff(diff, max_tokens, model)

    return diff


def commit_changes(message: str) -> bool:
    """
    Commit changes with the given message.

    Args:
        message: The commit message to use

    Returns:
        True if commit successful, False otherwise
    """
    return _git_operations.commit_changes(message)


def stage_files(files: List[str]) -> bool:
    """
    Stage files for commit.

    Args:
        files: List of files to stage (e.g., ["file1.py", "file2.py"])
               To stage all files, use ["."]

    Returns:
        True if successful, False otherwise
    """
    return _git_operations.stage_files(files)


def get_project_description() -> str:
    """
    Try to get a project description from common files and include repository name.

    Returns:
        A string description including repository name if available, or empty string if not found
    """
    return _git_operations.get_project_description()


def has_staged_changes() -> bool:
    """
    Check if there are staged changes.

    Returns:
        True if there are staged changes, False otherwise
    """
    return bool(get_staged_files())


def is_large_file(file_path: str, model: str = "anthropic:claude-3-5-haiku-latest") -> bool:
    """
    Check if a file should be treated as a large file based on its name and diff size.
    Kept for backward compatibility.

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


def get_file_diff(file_path: str, model: str = "anthropic:claude-3-5-haiku-latest") -> str:
    """
    Get the diff for a single file, with appropriate handling for large files.
    Kept for backward compatibility.

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
