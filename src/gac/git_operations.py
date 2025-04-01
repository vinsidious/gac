"""Git operations manager for GAC."""

import logging
import os
import subprocess
from typing import List, Optional

from gac.errors import GACError, convert_exception, handle_error
from gac.utils import print_error, print_info, print_success

logger = logging.getLogger(__name__)


class GitOperationsManager:
    """Class that manages git operations for the commit workflow."""

    def __init__(self, quiet: bool = False):
        """
        Initialize the GitOperationsManager.

        Args:
            quiet: Suppress non-error output
        """
        self.quiet = quiet

    def ensure_git_directory(self) -> Optional[str]:
        """
        Ensure we're in a git repository and change to the root directory if needed.

        Returns:
            The git repository root directory or None if not a git repository
        """
        try:
            # Try to get the git root directory
            git_dir = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            # Change to the git repository root if we're not already there
            current_dir = os.getcwd()
            if git_dir and git_dir != current_dir:
                logger.debug(f"Changing directory to git root: {git_dir}")
                os.chdir(git_dir)

            return git_dir

        except subprocess.CalledProcessError as e:
            # Not a git repository or other git error
            logger.error(f"Git error: {e}. Make sure you're in a git repository.")
            return None
        except Exception as e:
            logger.debug(f"Error determining git directory: {e}")
            # Continue with current directory
            return None

    def stage_all_files(self) -> bool:
        """
        Stage all files in the repository.

        Returns:
            True if successful, False otherwise
        """
        # Always show basic staging message
        if not self.quiet:
            print_info("Staging all changes...")
        else:
            if logging.getLogger().getEffectiveLevel() <= logging.INFO:
                logger.info("Staging all changes...")
        try:
            # Check if this is an empty repository
            status = self.get_status()
            is_empty_repo = "No commits yet" in status

            if is_empty_repo:
                if logging.getLogger().getEffectiveLevel() <= logging.INFO:
                    logger.info("Repository has no commits yet. Creating initial commit...")

                # First try to stage the files in the empty repo
                try:
                    # Use direct git command to stage files
                    subprocess.run(
                        ["git", "add", "."], check=True, capture_output=True, cwd=os.getcwd()
                    )
                    if logging.getLogger().getEffectiveLevel() <= logging.INFO:
                        logger.info("Files staged in empty repository")

                    # Now create the initial commit with staged files
                    commit_result = subprocess.run(
                        ["git", "commit", "-m", "Initial commit"],
                        check=True,
                        capture_output=True,
                        cwd=os.getcwd(),
                    )
                    if logging.getLogger().getEffectiveLevel() <= logging.INFO:
                        logger.info(f"Created initial commit: {commit_result.stdout}")
                    return True  # We've already staged and committed, no need to continue

                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to create initial commit with files: {e}")

                    # Try with an empty commit as fallback
                    try:
                        subprocess.run(
                            ["git", "commit", "--allow-empty", "-m", "Initial commit"],
                            check=True,
                            capture_output=True,
                            cwd=os.getcwd(),
                        )
                        if logging.getLogger().getEffectiveLevel() <= logging.INFO:
                            logger.info("Created empty initial commit")

                        # Now try to stage files again
                        subprocess.run(
                            ["git", "add", "."], check=True, capture_output=True, cwd=os.getcwd()
                        )
                        if logging.getLogger().getEffectiveLevel() <= logging.INFO:
                            logger.info("Files staged after initial commit")
                        return True

                    except subprocess.CalledProcessError as inner_e:
                        logger.error(f"Failed to create empty initial commit: {inner_e}")
                        # Continue anyway, maybe stage_files will work

            # Normal case - just stage all files
            success = self.stage_files(["."])
            if success:
                if not self.quiet:
                    print_success("All changes staged")
                elif logging.getLogger().getEffectiveLevel() <= logging.INFO:
                    logger.info("All changes staged")
                return True
            else:
                logger.error("Failed to stage changes")
                return False

        except Exception as e:
            error = convert_exception(e, GACError, "Failed to stage changes")
            handle_error(error, quiet=self.quiet, exit_program=False)
            return False

    def get_status(self) -> str:
        """
        Get git status.

        Returns:
            Git status output as string
        """
        try:
            return subprocess.run(
                ["git", "status"], capture_output=True, text=True, check=True
            ).stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get git status: {e}")
            return ""

    def get_staged_files(self) -> List[str]:
        """
        Get list of staged files.

        Returns:
            List of staged file paths
        """
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            return [line.strip() for line in output.splitlines() if line.strip()]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get staged files: {e}")
            return []

    def get_staged_diff(self) -> str:
        """
        Get the diff of staged changes.

        Returns:
            Git diff output as string
        """
        try:
            return subprocess.run(
                ["git", "diff", "--cached"], capture_output=True, text=True, check=True
            ).stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get staged diff: {e}")
            return ""

    def stage_files(self, files: List[str]) -> bool:
        """
        Stage specified files.

        Args:
            files: List of file paths to stage

        Returns:
            True if successful, False otherwise
        """
        try:
            for file in files:
                subprocess.run(["git", "add", file], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stage files: {e}")
            return False

    def commit_changes(self, commit_message: str) -> bool:
        """
        Commit staged changes with the given message.

        Args:
            commit_message: The commit message to use

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    def push_changes(self) -> bool:
        """
        Push committed changes to the remote repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.quiet:
                print_info("Pushing changes to remote...")
            elif logging.getLogger().getEffectiveLevel() <= logging.INFO:
                logger.info("Pushing changes to remote...")

            subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
                check=True,
            )

            if not self.quiet:
                print_success("Changes pushed successfully")
            elif logging.getLogger().getEffectiveLevel() <= logging.INFO:
                logger.info("Changes pushed successfully")

            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to push changes: {e.stderr.strip()}"
            logger.error(error_msg)
            if not self.quiet:
                print_error(error_msg)
            return False
