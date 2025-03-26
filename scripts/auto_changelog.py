# flake8: noqa: E501
"""Script to automate updating the ## [Unreleased] section of CHANGELOG.md based on changes since the last version release.

This script:
1. Determines the latest version tag.
2. Retrieves the git diff since that tag.
3. Retrieves the commit log since that tag.
4. Uses an LLM via the scoutie module to update or create the `## [Unreleased]` section in CHANGELOG.md.
5. Ensures markdown lint rules are followed (empty line around headers and lists).

Example usage:
```
# Update CHANGELOG.md with changes since the last tag
python scripts/auto_changelog.py

# Run in test mode without modifying the file
python scripts/auto_changelog.py --test

# Force update even if no changes are detected
python scripts/auto_changelog.py --force

# Specify a different changelog path
python scripts/auto_changelog.py --changelog path/to/CHANGELOG.md
```
"""

import logging
import re
import subprocess
from typing import List, Tuple

import click
from rich.logging import RichHandler

from gac.ai_utils import chat, count_tokens

logger = logging.getLogger(__name__)

MODEL = "anthropic:claude-3-5-haiku-latest"

guiding_principles = """
You are a helpful assistant that writes clear, concise changelog entries according to the following guidelines.

# How to structure the Unreleased section?

- There is a `## [Unreleased]` section in the changelog to accumulate changes since the last version release.
- The Unreleased section should follow the same principles as a versioned changelog entry:
  - Changes should be grouped by type: Added, Changed, Deprecated, Removed, Fixed, Security.
  - Changes within each group should be listed in order of importance, with the most significant changes first.
  - If no changes of a particular type, omit that section.
  - Keep it concise, but descriptive enough to understand the changes.
  - Do not include any version number or date in the Unreleased section. It is always titled `## [Unreleased]`.
- Feel free to modify or remove existing items in the Unreleased section if they are no longer accurate.
  - For example, if a change was previously reported but has since been reverted, remove it.
  - If a change has been modified or refined, update its description accordingly.
- The changelog is for humans, not machines.
- Follow Semantic Versioning conventions when categorizing changes, but do NOT produce a version number here.
- Do not output the entire changelog, only the updated `## [Unreleased]` section.
- Follow Markdown lint rules
- Put a blank line before and after each heading.
- Put a blank line before and after each list (the bullet points).
- Use **bold** text sparingly to emphasize only the most important information.
- Avoid vague statements; focus on specific, actionable insights backed by data or quotes.
- Exclude meta-commentary or notes about the summary itself.
- Incorporate descriptive emojis to enhance key points and make the report engaging.
- Place emojis at the beginning of lines unless they are part of a sentence.
- Use Markdown styling for headings, lists, and emphasis.
- Ensure every heading starts with emojis immediately after the #, ##, or ### symbols.
- For the title (#), use three emojis. For all major headings (##), use two emojis consistently. For subheadings (###), use one emoji.
- Include specific names and distinguishing features of products or developments, such as chatbots or image generators.
- Example format:

```

## [Unreleased]

### Added

- New feature 1
- New feature 2

### Changed

- Updated feature 1
- Updated feature 2

### Deprecated

- Deprecated feature 1
- Deprecated feature 2

### Removed

- Removed feature 1
- Removed feature 2

### Fixed

- Fixed bug 1
- Fixed bug 2

### Security

- Security update 1
- Security update 2

```

Note: Ensure each heading (e.g. `## [Unreleased]`, `### Added`) is surrounded by blank lines, and each list of items has a blank line before and after the block of items.
"""


def run_subprocess(command: List[str]) -> str:
    logger.info(f"Running command: `{' '.join(command)}`")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.error(f"Error running command: `{result.stderr}`")
        return ""

    if result.stdout:
        logger.debug(f"Command output:\n{result.stdout}")
    return result.stdout.strip()


def get_latest_tag() -> str:
    """Get the latest version tag."""
    tag = run_subprocess(["git", "describe", "--tags", "--abbrev=0"])
    logger.info(f"Latest tag: {tag}")
    return tag


def get_diff_since_tag(tag: str) -> str:
    """Get diff since the provided tag."""
    diff = run_subprocess(["git", "diff", f"{tag}..HEAD"])
    if diff is None:
        logger.error("Error getting diff.")
        return ""
    logger.info(f"Diff length: {len(diff)} characters")
    logger.info(f"Diff token count: {count_tokens(diff, MODEL)} tokens")
    return diff


def get_commits_since_tag(tag: str) -> List[str]:
    """Get commit log since the provided tag."""
    commits = run_subprocess(["git", "log", f"{tag}..HEAD", "--pretty=format:%s"])
    if commits is None:
        logger.error("Error getting commit log.")
        return []
    commit_list = commits.splitlines()
    logger.info(f"Found {len(commit_list)} commits since {tag}.")
    return commit_list


def read_changelog(changelog_path: str = "CHANGELOG.md") -> str:
    """Read the existing CHANGELOG.md."""
    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        logger.warning(f"{changelog_path} not found. Creating a new one.")
        return ""


def extract_unreleased_section(existing_changelog: str) -> Tuple[str, int, int]:
    """
    Extract the current Unreleased section if it exists.
    Returns the section content (without the '## [Unreleased]' heading) and the start/end indices.
    If not found, returns (None, None, None).
    """
    pattern = r"(## \[Unreleased\]\s*(?:\r?\n)(.*?)(?=## \[|$))"
    # Use DOTALL to match across multiple lines
    match = re.search(pattern, existing_changelog, flags=re.DOTALL)
    if match:
        section = match.group(1)  # entire matched block including heading
        content_only = match.group(2).strip() if match.group(2) else ""
        start = match.start(1)
        end = match.end(1)
        return content_only, start, end
    return None, None, None


def update_unreleased_section(
    latest_tag: str, diff: str, commits: List[str], existing_changelog: str
) -> str:
    """
    Send the diff and commits to the LLM and ask it to produce ONLY the updated `## [Unreleased]` section.
    If an Unreleased section exists, provide its current content as context.
    """
    unreleased_content, _, _ = extract_unreleased_section(existing_changelog)
    unreleased_content = unreleased_content if unreleased_content else ""
    logger.debug(f"Unreleased content: {unreleased_content}")

    commits_formatted = "\n".join(f"- {c}" for c in commits)

    top_context = (
        f"Below is the current Unreleased section:\n\n{unreleased_content}"
        if unreleased_content
        else "No Unreleased section exists yet."
    )

    prompt = f"""We have a CHANGELOG file that may or may not have an `## [Unreleased]` section. 
You will update or create the `## [Unreleased]` section based on recent changes.

Feel free to modify or remove existing items in the Unreleased section if they are no longer accurate. For example:
- If a change was previously reported but has since been reverted, remove it
- If a change has been modified or refined, update its description accordingly

List changes in order of importance within each category (Added, Changed, etc.), with the most significant changes first.

Do not output the entire changelog, only the updated `## [Unreleased]` section. 
No version numbers or dates should be included here, just `## [Unreleased]` and the categorized list of changes.

```
{top_context}
```

Here are the commits since the last release ({latest_tag}):

```
{commits_formatted}
```

Here is the diff since {latest_tag}:

```
{diff}
```

IMPORTANT: You MUST ONLY output the final `## [Unreleased]` section with no commentary or explanation.
"""
    logger.info(f"Prompt:\n{prompt}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    logger.info(f"Prompt token count: {count_tokens(prompt, MODEL):,}")

    messages = [
        {"role": "system", "content": guiding_principles},
        {"role": "user", "content": prompt},
    ]
    response = chat(messages, model=MODEL)
    logger.info(f"Response length: {len(response)} characters")
    logger.info(f"Response token count: {count_tokens(response, MODEL):,}")

    return response


def insert_or_replace_unreleased(changelog_path: str, new_section: str) -> None:
    """
    Insert or replace the `## [Unreleased]` section in the CHANGELOG.
    If it doesn't exist, place it at the top after the main title if present, else just at the top.
    """
    existing = read_changelog(changelog_path)

    new_section = new_section.strip()

    # Ensure that `## [Unreleased]` has blank lines before and after if it doesn't already
    # The LLM should handle this, but just to be safe:
    if not new_section.startswith("## [Unreleased]"):
        new_section = "## [Unreleased]\n\n" + new_section
    # Ensure a blank line at the end
    if not new_section.endswith("\n"):
        new_section += "\n"

    unreleased_content, start, end = extract_unreleased_section(existing)
    if unreleased_content is not None:
        # Replace existing Unreleased section
        pattern = r"(## \[Unreleased\]\s*(?:\r?\n)(.*?)(?=## \[|$))"
        updated = re.sub(pattern, new_section + "\n", existing, flags=re.DOTALL)
    else:
        # Insert at top, after "Changelog" title if exists
        if "# Changelog" in existing:
            parts = existing.split("# Changelog", 1)
            updated = f"# Changelog\n\n{new_section}\n{parts[1].strip()}\n"
        else:
            updated = f"# Changelog\n\n{new_section}\n{existing}"

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(updated)
    logger.info("CHANGELOG.md updated with the updated Unreleased section.")


def main(changelog_path: str, test_mode: bool = False, force: bool = False) -> None:
    latest_tag = get_latest_tag()
    if not latest_tag:
        logger.error("Failed to get latest tag.")
        return

    diff = get_diff_since_tag(latest_tag)
    if diff is None:
        logger.info("No diff found. Nothing to update in CHANGELOG.")
        return

    commits = get_commits_since_tag(latest_tag)
    if commits is None:
        logger.info("No commits found. Nothing to update in CHANGELOG.")
        return

    existing_changelog = read_changelog(changelog_path)

    if test_mode:
        logger.info("[TEST MODE ENABLED] Using example Unreleased section")
        new_section = """## [Unreleased]

### Added

- Example change from test mode

"""
    else:
        new_section = update_unreleased_section(latest_tag, diff, commits, existing_changelog)
        if not new_section:
            logger.info("No Unreleased section generated by the model.")
            return

    logger.info("Suggested Unreleased Section:")
    logger.info("")
    logger.info(new_section)
    logger.info("")

    if not force:
        response = input(
            "Do you want to insert/update this Unreleased section in the CHANGELOG? (y/n): "
        )
        if response.lower() != "y":
            logger.info("Aborted!")
            return

    insert_or_replace_unreleased(changelog_path, new_section)
    logger.info("CHANGELOG.md updated successfully!")


@click.command()
@click.option("--changelog", "-c", default="CHANGELOG.md", help="Path to the CHANGELOG file")
@click.option("--test", "-t", is_flag=True, help="Run in test mode with example output")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt and force update")
def cli(changelog, test, force):
    main(changelog, test_mode=test, force=force)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    cli()
