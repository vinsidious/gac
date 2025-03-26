#!/usr/bin/env python3
"""Script to automate writing quality commit messages.

This script sends the staged diff to an LLM for summarization and suggests a commit message.
It then prompts the user to proceed with the commit, runs pre-commit hooks, and commits the changes.

This script assumes that your environment has git, black, and isort installed.
It also assumes that your environment has pre-commit installed and configured.

# TODO:
- How to handle pre-commit/git hooks?
- Add support for custom commit message templates?
- Implement error handling for network failures
- Add option to specify commit type (e.g., feat, fix, docs)
- Ask user if they want to commit staged files that have unstaged changes

"""

import logging
import os
from typing import Optional

import click
from dotenv import load_dotenv
from rich.logging import RichHandler

from gac.ai_utils import chat, count_tokens
from gac.config import get_config
from gac.git import (
    commit_changes,
    get_existing_staged_python_files,
    get_staged_files,
    get_staged_python_files,
    stage_files,
)
from gac.utils import run_subprocess

load_dotenv()

logger = logging.getLogger(__name__)


def run_black() -> bool:
    """
    Run black code formatter on staged Python files.

    Returns:
        True if files were formatted, False otherwise
    """
    logger.debug("Identifying Python files for formatting with black...")
    python_files = get_existing_staged_python_files()
    if not python_files:
        logger.info("No existing Python files to format with black.")
        return False
    n_before = len(python_files)
    run_subprocess(["black"] + python_files)
    logger.debug("Checking which files were modified by black...")
    formatted_files = get_staged_python_files()
    n_formatted = n_before - len(formatted_files)
    logger.info(f"Black formatted {n_formatted} files.")
    return n_formatted > 0


def run_isort() -> bool:
    """
    Run isort import sorter on staged Python files.

    Returns:
        True if files were formatted, False otherwise
    """
    logger.debug("Identifying Python files for import sorting with isort...")
    python_files = get_existing_staged_python_files()
    if not python_files:
        logger.info("No existing Python files to format with isort.")
        return False
    n_before = len(python_files)
    run_subprocess(["isort"] + python_files)
    logger.debug("Checking which files were modified by isort...")
    formatted_files = get_staged_python_files()
    n_formatted = n_before - len(formatted_files)
    logger.info(f"isort formatted {n_formatted} files.")
    return n_formatted > 0


def send_to_llm(status: str, diff: str) -> str:
    """
    Send the git status and staged diff to an LLM for summarization.

    Args:
        status: Output of git status
        diff: Output of git diff --staged

    Returns:
        The generated commit message
    """
    config = get_config()
    model = config["model"]
    # fmt: off
    # flake8: noqa: E501
    prompt = (
        "Analyze this git status and git diff and write ONLY a commit message in the following format. "
        "Do not include any other text, explanation, or commentary.\n\n"
        "Format:\n"
        "[type]: Short summary of changes (50 chars or less)\n"
        " - Bullet point details about the changes\n"
        " - Another bullet point if needed\n\n"
        "[feat/fix/docs/refactor/test/chore/other]: <description>\n\n"
        "For larger changes, include bullet points:\n"
        "[category]: Main description\n"
        " - Change 1\n"
        " - Change 2\n"
        " - Change 3\n\n"
        "Git Status:\n"
        "```\n"
        + status
        + "\n```\n\n"
        "Git Diff:\n"
        "```\n"
        + diff
        + "\n```"
    )
    # fmt: on

    logger.info(f"Using model: {model}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    token_count = count_tokens(prompt, model)
    logger.info(f"Prompt token count: {token_count:,}")

    system = "You are a helpful assistant that writes clear, concise git commit messages. Only output the commit message, nothing else."
    messages = [{"role": "user", "content": prompt}]
    response = chat(
        messages=messages,
        model=model,
        temperature=0.7,
        system=system,
        test_mode=False,
    )

    response_token_count = count_tokens(response, model)
    logger.info(f"Response token count: {response_token_count:,}")
    return response


def main(
    test_mode: bool = False,
    force: bool = False,
    add_all: bool = False,
    no_format: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Main function to generate and apply a commit message.

    Args:
        test_mode: If True, use a test message without calling an LLM
        force: If True, skip user confirmation prompts
        add_all: If True, stage all changes before committing
        no_format: If True, skip code formatting
        quiet: If True, reduce output verbosity
        verbose: If True, increase output verbosity
        model: Override default model (format: provider:model)

    Returns:
        The commit message if successful, None otherwise
    """
    config = get_config()

    # Set logging level
    if verbose:
        logger.setLevel(logging.DEBUG)
    elif quiet:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    # Override model if specified
    if model:
        os.environ["GAC_MODEL"] = model

    if add_all:
        stage_files(["."])
        logger.info("All changes staged.")

    logger.debug("Checking for staged files to commit...")
    staged_files = get_staged_files()
    if len(staged_files) == 0:
        logger.info("No staged files to commit.")
        return None

    if test_mode:
        logger.info("[TEST MODE ENABLED] Using example commit message")
        commit_message = """[TEST MESSAGE] Example commit format
[feat]: This is a test commit message to demonstrate formatting
 - This is a test bullet point
 - Another test bullet point
 - Final test bullet point for demonstration"""
    else:
        logger.debug("Checking for Python files to format...")
        python_files = get_staged_python_files()
        existing_python_files = get_existing_staged_python_files()

        # Only run formatting if enabled and there are Python files
        if existing_python_files and config["use_formatting"] and not no_format:
            run_black()
            logger.debug("Re-staging Python files after black formatting...")
            existing_python_files = get_existing_staged_python_files()
            if existing_python_files:
                stage_files(existing_python_files)
            else:
                logger.info("No existing Python files to re-stage after black.")
            run_isort()
            logger.debug("Re-staging Python files after isort formatting...")
            existing_python_files = get_existing_staged_python_files()
            if existing_python_files:
                stage_files(existing_python_files)
            else:
                logger.info("No existing Python files to re-stage after isort.")

        logger.info("Generating commit message...")
        status = run_subprocess(["git", "status"])
        diff = run_subprocess(["git", "--no-pager", "diff", "--staged"])
        commit_message = send_to_llm(status=status, diff=diff)

    if not commit_message:
        logger.error("Failed to generate commit message.")
        return None

    print("\n=== Suggested Commit Message ===")
    print(f"{commit_message}")
    print("================================\n")

    if force:
        proceed = "y"
    else:
        prompt = "Do you want to proceed with this commit? (y/n): "
        proceed = click.prompt(prompt, type=str, default="y").strip().lower()

    if not proceed or proceed[0] != "y":
        logger.info("Commit aborted.")
        return None

    if test_mode:
        logger.info("[TEST MODE] Commit simulation completed. No actual commit was made.")
        return commit_message

    commit_changes(commit_message)
    logger.info("Changes committed successfully.")

    if force:
        push = "y"
    else:
        prompt = "Do you want to push these changes? (y/n): "
        push = click.prompt(prompt, type=str, default="y").strip().lower()

    if push and push[0] == "y":
        run_subprocess(["git", "push"])
        logger.info("Push complete.")
    else:
        logger.info("Push aborted.")

    return commit_message


@click.command()
@click.option("--test", "-t", is_flag=True, help="Run in test mode")
@click.option(
    "--force",
    "-f",
    "-y",
    is_flag=True,
    help="Force commit without user prompting (yes to all prompts)",
)
@click.option("--add-all", "-a", is_flag=True, help="Stage all changes before committing")
@click.option("--quiet", "-q", is_flag=True, help="Reduce output verbosity")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity")
@click.option("--no-format", "-nf", is_flag=True, help="Disable formatting")
@click.option("--model", "-m", help="Override default model (format: provider:model)")
def cli(
    test: bool, force: bool, add_all: bool, quiet: bool, verbose: bool, no_format: bool, model: str
) -> None:
    """Commit staged changes with an AI-generated commit message."""
    # Configure logging based on verbosity options
    log_level = logging.WARNING if quiet else (logging.DEBUG if verbose else logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    # Run the main function
    main(
        test_mode=test,
        force=force,
        add_all=add_all,
        no_format=no_format,
        quiet=quiet,
        verbose=verbose,
        model=model,
    )


if __name__ == "__main__":
    cli()
