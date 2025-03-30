#!/usr/bin/env python3
"""
Script to automate updating the ## [Unreleased] section of CHANGELOG.md based on changes
since the last version release.

This script:
1. Determines the latest version tag
2. Retrieves the git diff since that tag
3. Retrieves the commit log since that tag
4. Uses an LLM to update or create the `## [Unreleased]` section in CHANGELOG.md
5. Ensures markdown lint rules are followed

Features:
- Smart token management to optimize LLM requests
- Backup creation before modifying the changelog
- Configurable prompts and models
- Error recovery mechanisms
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import click
import yaml
from rich.logging import RichHandler

# Add project root to path for importing gac modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from gac.ai_utils import chat, count_tokens

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL = "anthropic:claude-3-5-haiku-latest"
MAX_TOKEN_LIMIT = 16000  # Maximum tokens to send to the LLM
CONFIG_FILE = Path(__file__).parent / "changelog_config.yaml"


class ChangelogError(Exception):
    """Custom exception for changelog-related errors."""

    pass


def load_config() -> Dict:
    """
    Load configuration from YAML file if it exists, otherwise use defaults.

    Returns:
        Dict: Configuration dictionary
    """
    config = {
        "model": os.environ.get("GAC_MODEL", DEFAULT_MODEL),
        "max_tokens": MAX_TOKEN_LIMIT,
        "temperature": 0.7,
        "categories": ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"],
        "prompt_file": str(Path(__file__).parent / "changelog_prompt.md"),
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                user_config = yaml.safe_load(f)
                if user_config and isinstance(user_config, dict):
                    config.update(user_config)
        except Exception as e:
            logger.warning(f"Error loading config file: {e}. Using defaults.")

    return config


def load_prompt_template() -> str:
    """
    Load the prompt template from file or use the default.

    Returns:
        str: The prompt template
    """
    config = load_config()
    prompt_file = config.get("prompt_file")

    if prompt_file and os.path.exists(prompt_file):
        try:
            with open(prompt_file, "r") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Error loading prompt file: {e}. Using default prompt.")

    # Return the default prompt if file doesn't exist or has an error
    return """
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
- Follow Markdown lint rules
- Put a blank line before and after each heading.
- Put a blank line before and after each list (the bullet points).
- Use **bold** text sparingly to emphasize only the most important information.
- Place emojis at the beginning of lines unless they are part of a sentence.
- Use Markdown styling for headings, lists, and emphasis.
"""


def run_subprocess(command: List[str]) -> str:
    """
    Run a subprocess command and return its output.

    Args:
        command: List of command arguments

    Returns:
        Command output as string

    Raises:
        ChangelogError: If the command fails
    """
    logger.debug(f"Running command: `{' '.join(command)}`")
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(command)}\nError: {e.stderr}"
        logger.error(error_msg)
        raise ChangelogError(error_msg)


def get_latest_tag() -> str:
    """
    Get the latest version tag from the repository.

    Returns:
        The latest version tag

    Raises:
        ChangelogError: If no tags are found
    """
    try:
        tag = run_subprocess(["git", "describe", "--tags", "--abbrev=0"])
        logger.info(f"Latest tag: {tag}")
        return tag
    except ChangelogError:
        raise ChangelogError("No version tags found. Please create an initial version tag.")


def get_diff_since_tag(tag: str) -> str:
    """
    Get diff since the provided tag.

    Args:
        tag: Git tag to get diff from

    Returns:
        The git diff as string

    Raises:
        ChangelogError: If getting diff fails
    """
    try:
        diff = run_subprocess(["git", "diff", f"{tag}..HEAD"])
        if not diff:
            logger.warning("No changes detected in git diff.")
            return ""

        logger.info(f"Diff length: {len(diff)} characters")
        token_count = count_tokens(diff, DEFAULT_MODEL)
        logger.info(f"Diff token count: {token_count} tokens")

        # If diff is too large, truncate it
        config = load_config()
        max_tokens = config.get("max_tokens", MAX_TOKEN_LIMIT)
        if token_count > max_tokens:
            logger.warning(
                f"Diff is too large ({token_count} tokens). "
                f"Truncating to approximately {max_tokens} tokens."
            )
            # Simple truncation - in a real implementation, you might want to be smarter
            # about how you truncate to keep the most relevant parts
            ratio = max_tokens / token_count
            char_limit = int(len(diff) * ratio)
            return diff[:char_limit] + "\n...[diff truncated due to length]..."

        return diff
    except ChangelogError as e:
        logger.error(f"Error getting diff: {e}")
        return ""
