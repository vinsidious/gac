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
from gac.formatting.formatters import run_black, run_isort
from gac.git import (
    commit_changes,
    get_existing_staged_python_files,
    get_project_description,
    get_staged_files,
    get_staged_python_files,
    stage_files,
)
from gac.utils import run_subprocess

load_dotenv()

logger = logging.getLogger(__name__)


def build_prompt(status: str, diff: str, one_liner: bool = False, hint: str = "") -> str:
    """Build LLM prompt from git status and diff."""
    # fmt: off
    # flake8: noqa: E501
    hint_text = f"\nPlease consider this context from the user: {hint}\n" if hint else ""
    
    if one_liner:
        prompt = (
            "Analyze this git status and git diff and write ONLY a commit message as a single line. "
            "Do not include any other text, explanation, or commentary.\n\n"
            "Format:\n"
            "[type]: Short summary of changes (50 chars or less)\n\n"
            "[feat/fix/docs/refactor/test/chore/other]: <description>"
            f"{hint_text}\n"
            "Git Status (git status -s):\n"
            "```\n"
            + status
            + "\n```\n\n"
            "Git Diff:\n"
            "```\n"
            + diff
            + "\n```"
        )
    else:
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
            " - Change 3"
            f"{hint_text}\n"
            "Git Status (git status -s):\n"
            "```\n"
            + status
            + "\n```\n\n"
            "Git Diff:\n"
            "```\n"
            + diff
            + "\n```"
        )
    # fmt: on
    return prompt


def send_to_llm(
    status: str,
    diff: str,
    one_liner: bool = False,
    show_prompt: bool = False,
    hint: str = "",
) -> str:
    """
    Send the git status and staged diff to an LLM for summarization.

    Args:
        status: Output of git status
        diff: Output of git diff --staged
        one_liner: If True, request a single-line commit message
        show_prompt: If True, display the prompt sent to the LLM
        hint: Optional context to include in the prompt (like "JIRA-123")

    Returns:
        The generated commit message
    """
    config = get_config()
    model = config["model"]

    prompt = build_prompt(status, diff, one_liner, hint)

    logger.info(f"Using model: {model}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    token_count = count_tokens(prompt, model)
    logger.info(f"Prompt token count: {token_count:,}")

    if show_prompt:
        logger.info("\n=== LLM Prompt ===")
        logger.info(prompt)
        logger.info("==================")

    # Get project description and include it in context if available
    project_description = get_project_description()
    system = "You are a helpful assistant that writes clear, concise git commit messages. Only output the commit message, nothing else."

    # Add project description to system message if available
    if project_description:
        system = f"You are a helpful assistant that writes clear, concise git commit messages for the following project: '{project_description}'. Only output the commit message, nothing else."

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
    one_liner: bool = False,
    show_prompt: bool = False,
    test_with_real_diff: bool = False,
    testing: bool = False,  # Used only during test suite runs
    hint: str = "",
):
    """Generate and apply a commit message."""
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

    # Track if we're in simulation mode (for test mode with no real files)
    simulation_mode = False

    if len(staged_files) == 0:
        if test_mode:
            logger.info("No staged files found in test mode")
            if not force and not testing:
                prompt = "Would you like a simulated test experience? (y/n)"
                proceed = click.prompt(prompt, type=str, default="y").strip().lower()
                if not proceed or proceed[0] != "y":
                    logger.info("Test simulation cancelled")
                    return None

            # Create simulated data for test experience
            logger.info("Using simulated files for test experience")
            simulation_mode = True
            status = "M app.py\nA utils.py\nA README.md"
            diff = """diff --git a/app.py b/app.py
index 1234567..abcdefg 100644
--- a/app.py
+++ b/app.py
@@ -10,7 +10,9 @@ def main():
     # Process command-line arguments
     args = parse_args()
     
-    # Configure logging
+    # Configure logging with improved format
+    logging.basicConfig(level=logging.INFO)
+    logger.info("Starting application")
     
     # Load configuration
     config = load_config(args.config)
diff --git a/utils.py b/utils.py
new file mode 100644
index 0000000..fedcba9
--- /dev/null
+++ b/utils.py
@@ -0,0 +1,8 @@
+def parse_args():
+    \"\"\"Parse command line arguments.\"\"\"
+    parser = argparse.ArgumentParser()
+    parser.add_argument("--config", help="Path to config file")
+    return parser.parse_args()
+
+def load_config(path):
+    \"\"\"Load configuration from file.\"\"\"
diff --git a/README.md b/README.md
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/README.md
@@ -0,0 +1,3 @@
+# Sample Project
+
+This is a sample project for testing commit messages.
"""
            # Set simulated files to match the diff
            staged_files = ["app.py", "utils.py", "README.md"]
            # If test_with_real_diff was set, inform that we're using simulation instead
            if test_with_real_diff:
                logger.info("Using simulated diff instead of real diff (no staged files)")
        else:
            logger.info("No staged files to commit.")
            return None

    # Generate commit message (real or test)
    if test_mode:
        logger.info("[TEST MODE ENABLED] Using test commit message")

        if test_with_real_diff and not simulation_mode:
            logger.info("Using real git diff in test mode")
            status = run_subprocess(["git", "status"])
            diff = run_subprocess(["git", "--no-pager", "diff", "--staged"])

            # Build a test prompt and log info about it
            prompt = build_prompt(status, diff, one_liner, hint)
            logger.info(f"Test prompt length: {len(prompt)} characters")
            token_count = count_tokens(prompt, config["model"])
            logger.info(f"Test prompt token count: {token_count:,}")

            if show_prompt:
                logger.info("\n=== Test LLM Prompt ===")
                logger.info(prompt)
                logger.info("=======================")

        # Generate appropriate test message
        if one_liner:
            commit_message = "[feat]: Add support for OAuth2 authentication with multiple providers"
        else:
            commit_message = """[TEST MESSAGE] Example commit format
[feat]: This is a test commit message to demonstrate formatting
 - This is a test bullet point
 - Another test bullet point
 - Final test bullet point for demonstration"""

        print("\n=== Test Commit Message ===")
        print(f"{commit_message}")
        print("========================\n")
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
        commit_message = send_to_llm(
            status=status,
            diff=diff,
            one_liner=one_liner,
            show_prompt=show_prompt,
            hint=hint,
        )

        if not commit_message:
            logger.error("Failed to generate commit message.")
            return None

        print("\n=== Suggested Commit Message ===")
        print(f"{commit_message}")
        print("================================\n")

    # Process commit confirmation for both real and test modes
    if force or testing:
        proceed = "y"
    else:
        if test_mode and simulation_mode:
            prompt = "Would you like to simulate proceeding with this commit? (y/n)"
        else:
            prompt = "Do you want to proceed with this commit? (y/n)"
        proceed = click.prompt(prompt, type=str, default="y").strip().lower()

    if not proceed or proceed[0] != "y":
        logger.info("Commit aborted.")
        return None

    # Handle test mode or real commit
    if test_mode:
        if simulation_mode:
            logger.info("[SIMULATION] This is a simulated commit (no actual files committed)")

            # Simulate the push prompt as well
            if force or testing:
                push = "y"
            else:
                prompt = "Would you like to simulate pushing these changes? (y/n)"
                push = click.prompt(prompt, type=str, default="y").strip().lower()

            if push and push[0] == "y":
                logger.info("[SIMULATION] Push simulated successfully")
            else:
                logger.info("[SIMULATION] Push simulation aborted")
        else:
            logger.info("[TEST MODE] Commit simulation completed. No actual commit was made.")

            # Only show push prompt in test mode if not in simulation mode
            if force or testing:
                push = "y"
            else:
                prompt = "Do you want to push these changes? (y/n)"
                push = click.prompt(prompt, type=str, default="y").strip().lower()

            if push and push[0] == "y":
                logger.info("[TEST MODE] Push simulation completed. No actual push was made.")
            else:
                logger.info("Push aborted.")

        return commit_message

    # Real commit process
    commit_changes(commit_message)
    logger.info("Changes committed successfully.")

    if force or testing:
        push = "y"
    else:
        prompt = "Do you want to push these changes? (y/n)"
        push = click.prompt(prompt, type=str, default="y").strip().lower()

    if push and push[0] == "y":
        run_subprocess(["git", "push"])
        logger.info("Push complete.")
    else:
        logger.info("Push aborted.")

    return commit_message


@click.command()
@click.option("--test", "-t", is_flag=True, help="Use a test message without calling an LLM")
@click.option("--force", "-f", "-y", is_flag=True, help="Skip user confirmation prompts")
@click.option("--add-all", "-a", is_flag=True, help="Stage all changes before committing")
@click.option("--quiet", "-q", is_flag=True, help="Reduce output verbosity")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity")
@click.option("--no-format", "-nf", is_flag=True, help="Skip code formatting")
@click.option("--model", "-m", type=str, help="Override default model (format: provider:model)")
@click.option("--one-liner", "-o", is_flag=True, help="Generate a single-line commit message")
@click.option("--show-prompt", "-sp", is_flag=True, help="Show the prompt sent to the LLM")
@click.option(
    "--test-with-diff", is_flag=True, help="Use actual git diff with test mode (only with --test)"
)
@click.option(
    "--hint", "-h", type=str, help="Optional context to include in the prompt (like 'JIRA-123')"
)
def cli(
    test: bool,
    force: bool,
    add_all: bool,
    quiet: bool,
    verbose: bool,
    no_format: bool,
    model: str,
    one_liner: bool,
    show_prompt: bool,
    test_with_diff: bool,
    hint: str,
) -> None:
    """Commit staged changes with AI-generated message."""
    # Configure logging based on verbosity options
    log_level = logging.WARNING if quiet else (logging.DEBUG if verbose else logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    # If model option is provided, add to global config
    if model:
        os.environ["GAC_MODEL"] = model

    # Run the main function with options
    main(
        test_mode=test,
        force=force,
        add_all=add_all,
        no_format=no_format,
        quiet=quiet,
        verbose=verbose,
        model=model,
        one_liner=one_liner,
        show_prompt=show_prompt,
        test_with_real_diff=test_with_diff,
        hint=hint,
    )


if __name__ == "__main__":
    cli()
