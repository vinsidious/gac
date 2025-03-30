#!/usr/bin/env python3
"""
Prepares the CHANGELOG.md file for a release by moving content from the Unreleased
section to a new version section with the current date.

This script:
1. Validates the provided version number format
2. Creates a backup of the changelog file
3. Updates the changelog with a new version header
4. Adds a link reference for the new version
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime


def validate_version(version: str) -> bool:
    """
    Validate that the version string has the expected format.

    Args:
        version: The version string to validate

    Returns:
        bool: True if the version is valid, False otherwise
    """
    pattern = r"^v?\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?$"
    return re.match(pattern, version) is not None


def backup_file(file_path: str) -> str:
    """
    Create a backup of the file.

    Args:
        file_path: Path to the file to backup

    Returns:
        str: Path to the backup file
    """
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_changelog(file_path: str, new_version: str) -> bool:
    """
    Update the changelog file with a new version section.

    Args:
        file_path: Path to the CHANGELOG.md file
        new_version: New version to add to the changelog

    Returns:
        bool: True if successful, False otherwise
    """
    # Remove 'v' prefix if present for consistency in the file
    version_without_v = new_version[1:] if new_version.startswith("v") else new_version
    display_version = new_version if new_version.startswith("v") else f"v{new_version}"

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: Changelog file not found at {file_path}")
            return False

        # Create backup
        backup_path = backup_file(file_path)
        print(f"Created backup at {backup_path}")

        with open(file_path, "r") as file:
            content = file.read()

        # Check if Unreleased section exists
        if "## [Unreleased]" not in content:
            print("Error: Could not find ## [Unreleased] section in the changelog")
            return False

        # Add new version header after Unreleased section
        content = re.sub(
            r"(## \[Unreleased\]\n+)",
            f"\\1## [{version_without_v}] - {today}\n\n",
            content,
            count=1,
        )

        # Extract link format and add new one
        link_match = re.search(r"\[\d+\.\d+\.\d+\]:\s+(.*?)v\d+\.\d+\.\d+", content)
        if link_match:
            base_url = link_match.group(1)
            new_link = f"[{version_without_v}]: {base_url}{display_version}\n"

            # Insert before first link reference
            first_link = re.search(r"^\[\d+\.\d+\.\d+\]:", content, re.MULTILINE)
            if first_link:
                pos = first_link.start()
                content = content[:pos] + new_link + content[pos:]

        # Write updated content
        with open(file_path, "w") as file:
            file.write(content)

        return True

    except Exception as e:
        print(f"Error updating changelog: {e}")
        # Restore from backup if it was created
        if "backup_path" in locals():
            print(f"Restoring from backup {backup_path}")
            shutil.copy2(backup_path, file_path)
        return False


def main():
    """Main function to parse arguments and update the changelog."""
    parser = argparse.ArgumentParser(description="Prepare changelog for a new release.")
    parser.add_argument("changelog_file", help="Path to the CHANGELOG.md file")
    parser.add_argument("new_version", help="New version number (e.g., 0.5.0 or v0.5.0)")
    args = parser.parse_args()

    # Validate version format
    if not validate_version(args.new_version):
        print(
            f"Error: Invalid version format '{args.new_version}'. Expected format: 0.5.0 or v0.5.0"
        )
        sys.exit(1)

    # Update changelog
    if update_changelog(args.changelog_file, args.new_version):
        print(f"Successfully updated changelog for version {args.new_version}")
    else:
        print("Failed to update changelog")
        sys.exit(1)


if __name__ == "__main__":
    main()
