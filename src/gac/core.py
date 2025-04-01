"""Core functionality for GAC.

This module contains the main business logic for Git Auto Commit,
consolidating functionality that was previously spread across multiple modules.
"""

import logging
import os
from typing import List, Optional

from rich.panel import Panel

import gac.git as git
from gac.ai import generate_commit_message
from gac.config import get_config
from gac.errors import GACError, handle_error
from gac.format import format_files
from gac.prompt import build_prompt, clean_commit_message
from gac.utils import console

logger = logging.getLogger(__name__)


def generate_commit(
    staged_files: Optional[List[str]] = None,
    formatting: bool = True,
    model: Optional[str] = None,
    hint: str = "",
    one_liner: bool = False,
    show_prompt: bool = False,
    show_prompt_full: bool = False,
    quiet: bool = False,
    no_spinner: bool = False,
) -> Optional[str]:
    """
    Generate a commit message for staged changes.

    Args:
        staged_files: Optional list of staged files (if None, all staged files are used)
        formatting: Whether to format code
        model: Override model to use
        hint: Additional context for the prompt
        one_liner: Generate a single-line commit message
        show_prompt: Show an abbreviated version of the prompt
        show_prompt_full: Show the complete prompt
        quiet: Suppress non-error output
        no_spinner: Disable progress spinner during API calls

    Returns:
        The generated commit message or None if failed
    """
    try:
        # Ensure we're in a git repository
        if not git.ensure_git_directory():
            return None

        # Get staged files if not provided
        if staged_files is None:
            staged_files = git.get_staged_files()

        if not staged_files:
            logger.error("No staged changes found. Stage your changes with git add first.")
            return None

        # Format staged files if requested
        if formatting:
            formatted = format_files(staged_files, quiet)
            if formatted:
                # Re-stage the formatted files
                all_formatted = []
                for files in formatted.values():
                    all_formatted.extend(files)

                if all_formatted:
                    git.stage_files(all_formatted)

        # Get the diff of staged changes
        diff = git.get_staged_diff()
        if not diff:
            logger.error("No diff found for staged changes.")
            return None

        # Get git status
        status = git.get_status()

        # Build the prompt
        prompt = build_prompt(status, diff, one_liner, hint)

        # Show prompt if requested
        if show_prompt:
            # Create an abbreviated version
            abbrev_prompt = (
                prompt.split("DIFF:")[0] + "DIFF: [truncated - diff content omitted for brevity]"
            )
            logger.info("Prompt sent to LLM:\n%s", abbrev_prompt)

        if show_prompt_full:
            logger.info("Full prompt sent to LLM:\n%s", prompt)

        # Get configuration
        config = get_config()
        if model:
            config["model"] = model

        # Use the model from config
        model_to_use = config.get("model", "anthropic:claude-3-5-haiku-latest")

        # Always show a minimal message when generating the commit message
        if not quiet:
            # Split provider:model if applicable
            if ":" in model_to_use:
                provider, model_name = model_to_use.split(":", 1)
                print(f"Using model: {model_name} with provider: {provider}")
            else:
                print(f"Using model: {model_to_use}")

        # Generate the commit message
        temperature = float(config.get("temperature", 0.7))
        message = generate_commit_message(
            prompt,
            model=model_to_use,
            temperature=temperature,
            show_spinner=not no_spinner,
            test_mode="PYTEST_CURRENT_TEST" in os.environ,
        )

        # Clean and return the message
        if message:
            return clean_commit_message(message)
        return None

    except Exception as e:
        logger.error(f"Error generating commit message: {e}")
        return None


def commit_changes(
    message: Optional[str] = None,
    staged_files: Optional[List[str]] = None,
    force: bool = False,
    add_all: bool = False,
    formatting: bool = True,
    model: Optional[str] = None,
    hint: str = "",
    one_liner: bool = False,
    show_prompt: bool = False,
    show_prompt_full: bool = False,
    quiet: bool = False,
    no_spinner: bool = False,
    push: bool = False,
) -> Optional[str]:
    """
    Generate commit message and commit staged changes.

    Args:
        message: Optional pre-generated commit message
        staged_files: Optional list of staged files (if None, all staged files are used)
        force: Skip all confirmation prompts
        add_all: Stage all changes before committing
        formatting: Whether to format code
        model: Override model to use
        hint: Additional context for the prompt
        one_liner: Generate a single-line commit message
        show_prompt: Show an abbreviated version of the prompt
        show_prompt_full: Show the complete prompt
        quiet: Suppress non-error output
        no_spinner: Disable progress spinner during API calls
        push: Push changes to remote after committing

    Returns:
        The generated commit message or None if failed
    """
    try:
        # Ensure we're in a git repository
        if not git.ensure_git_directory():
            return None

        # Stage all files if requested
        if add_all:
            git.stage_all_files()

        # Get staged files
        if staged_files is None:
            staged_files = git.get_staged_files()

        if not staged_files:
            logger.error("No staged changes found. Stage your changes with git add first.")
            return None

        # Generate commit message if not provided
        if not message:
            message = generate_commit(
                staged_files=staged_files,
                formatting=formatting,
                model=model,
                hint=hint,
                one_liner=one_liner,
                show_prompt=show_prompt,
                show_prompt_full=show_prompt_full,
                quiet=quiet,
                no_spinner=no_spinner,
            )

        if not message:
            logger.error("Failed to generate commit message.")
            return None

        # Always display the commit message
        if not quiet:
            console.print("\nGenerated commit message:", style="info")
            console.print(Panel(message, title="Commit Message", border_style="bright_blue"))

        # If force mode is not enabled, prompt for confirmation
        if not force and not quiet:
            confirm = input("\nProceed with this commit message? (y/n): ").strip().lower()
            if confirm == "n":
                print("Commit canceled.")
                return None

        # Execute the commit
        success = git.commit_changes(message)
        if not success:
            handle_error(GACError("Failed to commit changes"), quiet=quiet)
            return None

        # Push changes if requested
        if push and success:
            push_success = git.push_changes()
            if not push_success:
                handle_error(GACError("Failed to push changes"), quiet=quiet, exit_program=False)

        return message

    except Exception as e:
        logger.error(f"Error during commit workflow: {e}")
        return None
