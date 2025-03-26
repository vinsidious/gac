"""
Script to automate the version release process.

This script:
1. Checks for uncommitted changes
2. Updates the version in .bumpversion.cfg and __about__.py
3. Updates the changelog
4. Creates and pushes the tag

Example usage:
```
# Release a new version
python scripts/auto_release.py

# Run in test mode without modifying files
python scripts/auto_release.py --test

# Force release even if no changes are detected
python scripts/auto_release.py --force

# Specify a different changelog path
python scripts/auto_release.py --changelog path/to/CHANGELOG.md
```
"""

import logging
import re
import subprocess
from typing import List

import click
from rich.logging import RichHandler

logger = logging.getLogger(__name__)

MODEL = "anthropic:claude-3-5-haiku-latest"


def run_subprocess(command: List[str]) -> str:
    """Run a subprocess command and return its output."""
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_latest_tag() -> str:
    """Get the latest version tag."""
    return run_subprocess(["git", "describe", "--tags", "--abbrev=0"])


def check_for_uncommitted_changes() -> bool:
    """Check if there are any uncommitted changes."""
    status = run_subprocess(["git", "status", "--porcelain"])
    return status != ""


def update_version_files(new_version: str) -> None:
    """Update the version in .bumpversion.cfg and __about__.py."""
    # Update .bumpversion.cfg
    with open(".bumpversion.cfg", "r") as f:
        content = f.read()
    content = re.sub(r"current_version = .+", f"current_version = {new_version}", content)
    with open(".bumpversion.cfg", "w") as f:
        f.write(content)

    # Update __about__.py
    with open("src/gac/__about__.py", "r") as f:
        content = f.read()
    content = re.sub(r"__version__ = .+", f'__version__ = "{new_version}"', content)
    with open("src/gac/__about__.py", "w") as f:
        f.write(content)


def create_and_push_tag(version: str) -> None:
    """Create and push the version tag."""
    run_subprocess(["git", "tag", version])
    run_subprocess(["git", "push", "origin", version])


def main(
    changelog_path: str = "CHANGELOG.md", test_mode: bool = False, force: bool = False
) -> None:
    """Main function to handle the release process."""
    # Check for uncommitted changes
    has_uncommitted_changes = check_for_uncommitted_changes()
    if not force and has_uncommitted_changes:
        logger.error("There are uncommitted changes. Please commit them first.")
        return
    # Warn about uncommitted changes if --force is used
    if force and has_uncommitted_changes:
        logger.warning(
            "Warning: Forcing a release with uncommitted changes. This may lead to inconsistencies and errors:\n"  # noqa: E501
            "- Local changes will NOT be included in the release.\n"
            "- Only version files (.bumpversion.cfg and __about__.py) will be updated and committed.\n"  # noqa: E501
            "- The released version may not match your local codebase.\n"
            "- Features, fixes, or dependencies in uncommitted changes will be missing from the release.\n\n"  # noqa: E501
            "Recommendations:\n"
            "1. Commit or stash your changes before releasing.\n"
            "2. Run 'git status' to review local changes.\n"
            "3. Consider re-running without --force.\n"
            "4. Seek guidance if unsure.\n\n"
            "Proceed with caution to avoid potential issues in the released version."
        )

    # Run tests before release
    if not test_mode:
        logger.info("Running tests before release...")
        test_result = run_subprocess(["python", "-m", "pytest", "tests/", "-v"])
        if test_result is None or "FAILED" in test_result:
            logger.error("Tests failed. Please fix the issues before proceeding with the release.")
            return
        logger.info("All tests passed successfully!")

    # Get the latest tag
    latest_tag = get_latest_tag()
    if not latest_tag:
        logger.error("No version tags found. Please create an initial version tag.")
        return

    # Update version files
    new_version = f"v{latest_tag.split('v')[-1]}"  # Remove 'v' prefix if present
    if not test_mode:
        update_version_files(new_version)
        run_subprocess(["git", "add", ".bumpversion.cfg", "src/gac/__about__.py"])
        run_subprocess(["git", "commit", "-m", f"Update version to {new_version} for release"])
        run_subprocess(["git", "push", "origin", "main"])

    # Create and push tag
    if not test_mode:
        create_and_push_tag(new_version)

    logger.info(f"Successfully released version {new_version}")


@click.command()
@click.option("--changelog", default="CHANGELOG.md", help="Path to the changelog file")
@click.option("--test", is_flag=True, help="Run in test mode without modifying files")
@click.option("--force", is_flag=True, help="Force release even if no changes are detected")
def cli(changelog: str, test: bool, force: bool) -> None:
    """CLI entry point for the release script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    main(changelog, test, force)


if __name__ == "__main__":
    cli()
