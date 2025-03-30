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
from gac.formatting.formatters import format_staged_files
from gac.git import (
    commit_changes,
    get_project_description,
    get_staged_diff,
    get_staged_files,
    stage_files,
)
from gac.utils import run_subprocess

load_dotenv()

logger = logging.getLogger(__name__)


def get_border_length(content: str, min_length: int = 0, max_length: int = 120) -> int:
    """Calculate the length of the border based on content.

    Args:
        content: The content to calculate border length for
        min_length: Minimum border length (default: 0)
        max_length: Maximum border length (default: 120)

    Returns:
        The calculated border length
    """
    # Get the longest line length
    max_line_length = max(len(line) for line in content.split("\n"))
    # Calculate border length (must be odd to maintain symmetry)
    border_length = max(min_length, max_line_length)
    # Cap at max_length
    border_length = min(border_length, max_length)
    return border_length


def build_prompt(status: str, diff: str, one_liner: bool = False, hint: str = "") -> str:
    """Build LLM prompt from git status and diff."""
    # Add hint to prompt if provided
    hint_text = f"\nPlease consider this context from the user: {hint}\n" if hint else ""

    # Base prompt components that are the same for both formats
    base_prompt = (
        "Analyze this git status and git diff and write ONLY a commit message. "
        "Do not include any other text, explanation, or commentary.\n\n"
        "Format:\n"
    )

    # Basic format shared by both modes
    format_desc = "[type]: Short summary of changes (50 chars or less)"

    # Additional format details for the detailed mode
    detail_format = (
        "\n - Bullet point details about the changes"
        "\n - Another bullet point if needed\n\n"
        "[feat/fix/docs/refactor/test/chore/other]: <description>\n\n"
        "For larger changes, include bullet points:\n"
        "[category]: Main description\n"
        " - Change 1\n"
        " - Change 2\n"
        " - Change 3"
    )

    # Command output sections (same for both modes)
    git_sections = (
        f"{hint_text}\n"
        "Git Status (git status -s):\n"
        "```\n" + status + "\n```\n\n"
        "Git Diff:\n"
        "```\n" + diff + "\n```"
    )

    # Build the final prompt based on one_liner flag
    if one_liner:
        format_section = (
            format_desc + "\n\n[feat/fix/docs/refactor/test/chore/other]: <description>"
        )
        prompt = base_prompt + format_section + git_sections
    else:
        format_section = format_desc + detail_format
        prompt = base_prompt + format_section + git_sections

    return prompt


def send_to_llm(
    status: str,
    diff: str,
    one_liner: bool = False,
    show_prompt: bool = False,
    hint: str = "",
    force: bool = False,
) -> str:
    """
    Send the git status and staged diff to an LLM for summarization.

    Args:
        status: Output of git status
        diff: Output of git diff --staged
        one_liner: If True, request a single-line commit message
        show_prompt: If True, display the prompt sent to the LLM
        hint: Optional context to include in the prompt (like "JIRA-123")
        force: If True, skip confirmation prompts

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

    # Check if token count exceeds the limit
    max_tokens = config["max_input_tokens"]
    if token_count > max_tokens:
        logger.warning(f"Warning: Prompt exceeds token limit ({token_count} > {max_tokens})")
        if not force:
            prompt_msg = (
                f"The prompt is {token_count:,} tokens, which exceeds the limit "
                f"of {max_tokens:,}. Continue anyway?"
            )
            if not click.confirm(prompt_msg, default=False):
                logger.info("Operation cancelled by user")
                return ""
    if show_prompt:
        border_length = get_border_length(prompt)
        header = "=== LLM Prompt ==="
        # Calculate padding ensuring equal sides
        total_padding = border_length - len(header)
        left_padding = (total_padding + 1) // 2
        right_padding = left_padding
        top_border = f"{'=' * left_padding}{header}{'=' * right_padding}"
        print(f"\n{top_border}")
        print(prompt)
        print("=" * border_length)

    # Get project description and include it in context if available
    project_description = get_project_description()
    system = (
        "You are a helpful assistant that writes clear, concise git commit messages. "
        "Only output the commit message, nothing else."
    )

    # Add project description to system message if available
    if project_description:
        system = (
            "You are a helpful assistant that writes clear, concise git commit messages "
            f"for the following project: '{project_description}'. "
            "Only output the commit message, nothing else."
        )

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
    else:
        logger.setLevel(logging.ERROR)

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
            print("*** SIMULATION MODE ***")
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

    # Track if we need to restore unstaged changes
    restore_unstaged = False

    # If there are unstaged changes, stash them temporarily
    if not no_format and not testing:
        has_unstaged_changes = run_subprocess(["git", "diff", "--quiet", "--cached", "--exit-code"])
        if not has_unstaged_changes:  # There are unstaged changes
            logger.debug("Stashing unstaged changes temporarily")
            run_subprocess(["git", "stash", "-k", "-q"])  # Keep index, quiet mode
            restore_unstaged = True

    # Format only the staged changes
    if not no_format and not testing:
        logger.info("Formatting staged files...")
        any_formatted, formatted_exts = format_staged_files(stage_after_format=True)
        if any_formatted:
            logger.info(f"Formatted files with extensions: {', '.join(formatted_exts)}")
        else:
            logger.debug("No files were formatted.")

    # Restore unstaged changes if needed
    if restore_unstaged:
        logger.debug("Restoring unstaged changes")
        try:
            run_subprocess(["git", "stash", "pop", "-q"])
        except Exception as e:
            logger.error(f"Failed to restore unstaged changes: {e}")

    if test_mode:
        if simulation_mode:
            print("*** SIMULATION MODE ***")
            commit_message = send_to_llm(
                status=status,
                diff=diff,
                one_liner=one_liner,
                show_prompt=show_prompt,
                hint=hint,
                force=force,
            )
        else:
            print("*** TEST MODE ***")
            status = run_subprocess(["git", "status"])
            diff, truncated_files = get_staged_diff()

            if truncated_files:
                logger.warning(f"Large files detected and truncated: {', '.join(truncated_files)}")
                if not force and not testing:
                    if not click.confirm(
                        "Some large files were truncated to reduce token usage. Continue?",
                        default=True,
                    ):
                        logger.info("Operation cancelled by user")
                        return None

            commit_message = send_to_llm(
                status=status,
                diff=diff,
                one_liner=one_liner,
                show_prompt=show_prompt,
                hint=hint,
                force=force,
            )
    else:
        logger.debug("Checking for files to format...")

        # Only run formatting if enabled
        if config["use_formatting"] and not no_format:
            any_formatted, formatted_exts = format_staged_files(stage_after_format=True)
            if any_formatted:
                logger.info(f"Formatted files with extensions: {', '.join(formatted_exts)}")
            else:
                logger.debug("No files were formatted.")

        logger.info("Generating commit message...")
        status = run_subprocess(["git", "status"])
        diff, truncated_files = get_staged_diff()

        if truncated_files:
            logger.warning(f"Large files detected and truncated: {', '.join(truncated_files)}")
            if not force and not testing:
                if not click.confirm(
                    "Some large files were truncated to reduce token usage. Continue?",
                    default=True,
                ):
                    logger.info("Operation cancelled by user")
                    return None

        commit_message = send_to_llm(
            status=status,
            diff=diff,
            one_liner=one_liner,
            show_prompt=show_prompt,
            hint=hint,
            force=force,
        )

    if not commit_message:
        logger.error("Failed to generate commit message.")
        return None
    border_length = get_border_length(commit_message)
    header = "=== Suggested Commit Message ==="
    # Calculate padding ensuring equal sides by rounding up
    total_padding = border_length - len(header)
    left_padding = (total_padding + 1) // 2
    right_padding = left_padding
    top_border = f"{'=' * left_padding}{header}{'=' * right_padding}"
    print(f"\n{top_border}")
    print(f"{commit_message}")
    print("=" * border_length + "\n")

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
            print("*** SIMULATION MODE ***")

            # Simulate the push prompt as well
            if force or testing:
                push = "y"
            else:
                prompt = "Would you like to simulate pushing these changes? (y/n)"
                push = click.prompt(prompt, type=str, default="y").strip().lower()

            if push and push[0] == "y":
                print("*** SIMULATION MODE: PUSH SIMULATED SUCCESSFULLY ***")
            else:
                print("*** SIMULATION MODE: PUSH SIMULATION ABORTED ***")
        else:
            print("*** TEST MODE ***")

            # Only show push prompt in test mode if not in simulation mode
            if force or testing:
                push = "y"
            else:
                prompt = "Do you want to push these changes? (y/n)"
                push = click.prompt(prompt, type=str, default="y").strip().lower()

            if push and push[0] == "y":
                print("*** TEST MODE: PUSH SIMULATION COMPLETED ***")
            else:
                print("*** TEST MODE: PUSH ABORTED ***")

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
