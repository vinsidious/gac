import logging
import os
import re
import subprocess
import sys
from enum import Enum
from typing import List, Optional, Tuple

import click
from rich.logging import RichHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

# Constants
VERSION_TYPES = ["patch", "minor", "major", "alpha", "beta", "rc"]
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL = "anthropic:claude-3-5-haiku-latest"


class ReleaseError(Exception):
    """Custom exception for release-related errors."""

    pass


class VersionType(str, Enum):
    """Enum for version bump types."""

    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"


def run_subprocess(command: List[str], check: bool = True) -> Optional[str]:
    """
    Run a subprocess command and return its output.

    Args:
        command: List of command arguments
        check: Whether to raise an exception on non-zero exit code

    Returns:
        Command output as string, or None if command fails and check=False

    Raises:
        ReleaseError: If the command fails and check=True
    """
    logger.debug(f"Running command: `{' '.join(command)}`")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(command)}\nError: {e.stderr}"
        if check:
            raise ReleaseError(error_msg)
        logger.error(error_msg)
        return None


def get_latest_tag() -> str:
    """
    Get the latest version tag from the repository.

    Returns:
        The latest version tag

    Raises:
        ReleaseError: If no tags are found
    """
    try:
        return run_subprocess(["git", "describe", "--tags", "--abbrev=0"])
    except ReleaseError:
        raise ReleaseError("No version tags found. Please create an initial version tag.")


def check_for_uncommitted_changes() -> bool:
    """
    Check if there are any uncommitted changes in the repository.

    Returns:
        True if there are uncommitted changes, False otherwise
    """
    status = run_subprocess(["git", "status", "--porcelain"])
    return status != ""


def run_tests() -> bool:
    """
    Run the test suite to ensure code quality.

    Returns:
        True if all tests pass, False otherwise
    """
    logger.info("Running tests before release...")
    try:
        output = run_subprocess(["python", "-m", "pytest", "tests/", "-v"], check=False)
        if output is None or "failed" in output.lower():
            logger.error("Tests failed. Please fix the issues before proceeding with the release.")
            return False
        logger.info("All tests passed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False


def get_current_version() -> str:
    """
    Get the current version from the project configuration.

    Returns:
        The current version string
    """
    try:
        with open(os.path.join(PROJECT_ROOT, "src/gac/__about__.py"), "r") as f:
            content = f.read()
            match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)

        # Alternative: use bump-my-version
        output = run_subprocess(["bump-my-version", "show", "--tag-value"], check=False)
        if output:
            return output.strip()

        raise ReleaseError("Could not determine current version")
    except Exception as e:
        raise ReleaseError(f"Error getting current version: {e}")


def update_changelog(version: str) -> bool:
    """
    Update the changelog for the new version.

    Args:
        version: The new version string

    Returns:
        True if successful, False otherwise
    """
    changelog_path = os.path.join(PROJECT_ROOT, "CHANGELOG.md")
    try:
        # Run the prep_changelog_for_release.py script
        script_path = os.path.join(PROJECT_ROOT, "scripts/prep_changelog_for_release.py")
        run_subprocess([sys.executable, script_path, changelog_path, version])
        logger.info(f"Updated changelog for version {version}")
        return True
    except Exception as e:
        logger.error(f"Error updating changelog: {e}")
        return False


def bump_version(version_type: str) -> Tuple[str, str]:
    """
    Bump the version using bump-my-version.

    Args:
        version_type: Type of version bump (patch, minor, major, etc.)

    Returns:
        Tuple containing old and new version strings

    Raises:
        ReleaseError: If version bump fails
    """
    old_version = get_current_version()

    try:
        output = run_subprocess(["bump-my-version", "bump", version_type])
        new_version = get_current_version()
        logger.info(f"Bumped version from {old_version} to {new_version}")
        return old_version, new_version
    except Exception as e:
        raise ReleaseError(f"Error bumping version: {e}")


def create_and_push_tag(version: str) -> bool:
    """
    Create and push the version tag.

    Args:
        version: The version string for the tag

    Returns:
        True if successful, False otherwise
    """
    try:
        # Format tag version (ensure it starts with v)
        tag_version = version if version.startswith("v") else f"v{version}"

        # Create tag
        run_subprocess(["git", "tag", tag_version])
        logger.info(f"Created tag {tag_version}")

        # Push tag
        run_subprocess(["git", "push", "origin", tag_version])
        logger.info(f"Pushed tag {tag_version} to origin")

        return True
    except Exception as e:
        logger.error(f"Error creating or pushing tag: {e}")
        return False


@click.command()
@click.option(
    "--type",
    "-t",
    type=click.Choice(VersionType.__members__.values(), case_sensitive=False),
    default=VersionType.PATCH.value,
    help="Type of version bump to perform",
)
@click.option("--test", is_flag=True, help="Run in test mode without modifying files")
@click.option("--force", "-f", is_flag=True, help="Force release even if no changes are detected")
@click.option("--changelog", default="CHANGELOG.md", help="Path to the changelog file")
def main(type: str, test: bool, force: bool, changelog: str) -> None:
    """Automate the version release process."""
    try:
        # Check for uncommitted changes
        has_uncommitted_changes = check_for_uncommitted_changes()
        if not force and has_uncommitted_changes:
            logger.error("There are uncommitted changes. Please commit them first.")
            sys.exit(1)

        # Warn about uncommitted changes if --force is used
        if force and has_uncommitted_changes:
            logger.warning(
                "Warning: Forcing a release with uncommitted changes. "
                "This may lead to inconsistencies and errors."
            )
            if not test and not click.confirm("Are you sure you want to proceed?", default=False):
                logger.info("Release cancelled.")
                sys.exit(0)

        if test:
            logger.info("Running in test mode - no files will be modified")
            old_version = get_current_version()
            # Simulate new version
            if old_version.startswith("v"):
                old_version = old_version[1:]
            v_parts = old_version.split(".")
            if type == VersionType.PATCH.value:
                v_parts[2] = str(int(v_parts[2]) + 1)
            elif type == VersionType.MINOR.value:
                v_parts[1] = str(int(v_parts[1]) + 1)
                v_parts[2] = "0"
            elif type == VersionType.MAJOR.value:
                v_parts[0] = str(int(v_parts[0]) + 1)
                v_parts[1] = "0"
                v_parts[2] = "0"
            new_version = ".".join(v_parts)
            logger.info(f"Would bump version from {old_version} to {new_version}")
            logger.info("Test run completed successfully")
            return

        # Run tests before release
        if not run_tests():
            if not click.confirm("Tests failed. Continue anyway?", default=False):
                sys.exit(1)

        # Bump version
        old_version, new_version = bump_version(type)

        # Update changelog
        if not update_changelog(new_version):
            if not click.confirm("Failed to update changelog. Continue anyway?", default=False):
                sys.exit(1)

        # Add and commit changes
        run_subprocess(["git", "add", "."])
        run_subprocess(["git", "commit", "-m", f"Release {new_version}"])

        # Push changes
        run_subprocess(["git", "push", "origin", "main"])

        # Create and push tag
        if not create_and_push_tag(new_version):
            logger.error("Failed to create or push tag, but version has been bumped.")
            sys.exit(1)

        logger.info(f"Successfully released version {new_version}")

    except Exception as e:
        logger.error(f"Release process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
