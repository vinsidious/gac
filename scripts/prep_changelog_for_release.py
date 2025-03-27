#!/usr/bin/env python3
import re
import sys
from datetime import datetime


def update_changelog(file_path, new_version):
    today = datetime.now().strftime("%Y-%m-%d")

    with open(file_path, "r") as file:
        content = file.read()

    # Add new version header after Unreleased section
    content = re.sub(
        r"(## \[Unreleased\]\n+)", f"\\1## [{new_version}] - {today}\n\n", content, count=1
    )

    # Extract link format from existing link and add new one
    link_match = re.search(r"\[0\.\d+\.\d+\]:\s+(.*?)v0\.\d+\.\d+", content)
    if link_match:
        base_url = link_match.group(1)
        new_link = f"[{new_version}]: {base_url}v{new_version}\n"

        # Insert before first link reference
        first_link = re.search(r"^\[0\.\d+\.\d+\]:", content, re.MULTILINE)
        if first_link:
            pos = first_link.start()
            content = content[:pos] + new_link + content[pos:]

    with open(file_path, "w") as file:
        file.write(content)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <changelog_file> <new_version>")
        sys.exit(1)

    update_changelog(sys.argv[1], sys.argv[2])
    print(f"Updated changelog for version {sys.argv[2]}")
