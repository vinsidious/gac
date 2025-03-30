#!/usr/bin/env python3
"""Main module for gac."""

import logging
import os
import sys
from typing import Optional

import click
from rich.panel import Panel

from gac.ai_utils import (
    AIError,
    APIAuthenticationError,
    APIConnectionError,
    APIRateLimitError,
    APITimeoutError,
    APIUnsupportedModelError,
    chat,
    count_tokens,
)
from gac.config import get_config
from gac.formatting import format_staged_files
from gac.git import (
    commit_changes,
    get_project_description,
    get_staged_diff,
    get_staged_files,
    stage_files,
)
from gac.utils import (
    console,
    format_bordered_text,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
    run_subprocess,
)

logger = logging.getLogger(__name__)


def build_prompt(
    status: str, diff: str, one_liner: bool = False, hint: str = "", conventional: bool = False
) -> str:
    """
    Build a prompt for the LLM to generate a commit message.

    Args:
        status: Output of git status
        diff: Output of git diff --staged
        one_liner: If True, request a single-line commit message
        hint: Optional context to include in the prompt (like "JIRA-123")
        conventional: If True, request a conventional commit format message

    Returns:
        The prompt string
    """
    prompt = []
    prompt.append(
        "Generate a meaningful and descriptive git commit message based on the following changes."
    )

    if one_liner:
        prompt.append("\nFormat it as a single line (50-72 characters if possible).")
    else:
        prompt.append(
            "\nFormat it with a concise summary line (50-72 characters) followed by a "
            "more detailed explanation if needed."
        )

    if conventional:
        prompt.append(
            "\nUse the Conventional Commits format: <type>(<optional scope>): <description>"
            "\nCommon types include:"
            "\n- feat: A new feature"
            "\n- fix: A bug fix"
            "\n- docs: Documentation changes"
            "\n- style: Changes that don't affect code meaning (formatting, whitespace)"
            "\n- refactor: Code changes that neither fix a bug nor add a feature"
            "\n- perf: Performance improvements"
            "\n- test: Adding or correcting tests"
            "\n- build: Changes to build system or dependencies"
            "\n- ci: Changes to CI configuration"
            "\n- chore: Other changes that don't modify src or test files"
            "\nChoose the most appropriate type based on the changes. Include a scope in "
            "parentheses if relevant."
            "\nFor breaking changes, add ! before the colon or include 'BREAKING CHANGE: "
            "description' in the footer."
        )

    if hint:
        prompt.append(f"\nInclude this context in your message: {hint}")

    prompt.append(
        "\nDo not include any explanation or preamble like 'Here's a commit message', etc."
    )
    prompt.append("Just output the commit message directly.")
    prompt.append("\n\nCurrent git status:")
    prompt.append("```")
    prompt.append(status)
    prompt.append("```")
    prompt.append("\nChanges to be committed:")
    prompt.append("```")
    prompt.append(diff)
    prompt.append("```")

    return "\n".join(prompt)


def send_to_llm(
    status: str,
    diff: str,
    one_liner: bool = False,
    show_prompt: bool = False,
    hint: str = "",
    force: bool = False,
    conventional: bool = False,
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
        conventional: If True, request a conventional commit format message

    Returns:
        The generated commit message
    """
    config = get_config()
    model = config["model"]

    prompt = build_prompt(status, diff, one_liner, hint, conventional)

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
        print(format_bordered_text(prompt, header="=== LLM Prompt ==="))

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

    try:
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

    except APIConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        print(
            format_bordered_text(
                "Failed to connect to the AI service. Please check your internet "
                "connection and try again.",
                header="=== CONNECTION ERROR ===",
            )
        )
        return ""

    except APITimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        print(
            format_bordered_text(
                "The AI service took too long to respond. Please try again later.",
                header="=== TIMEOUT ERROR ===",
            )
        )
        return ""

    except APIRateLimitError as e:
        logger.error(f"Rate limit error: {str(e)}")
        print(
            format_bordered_text(
                "Rate limit exceeded for the AI service. Please wait a few minutes and try again.",
                header="=== RATE LIMIT EXCEEDED ===",
            )
        )
        return ""

    except APIAuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        provider = model.split(":")[0] if ":" in model else "your AI"
        print(
            format_bordered_text(
                f"Authentication failed for {provider} API. Please check your API key and ensure "
                f"it's properly set in your environment variables.",
                header="=== AUTHENTICATION ERROR ===",
            )
        )
        return ""

    except APIUnsupportedModelError as e:
        logger.error(f"Model error: {str(e)}")
        print(
            format_bordered_text(
                f"The model '{model}' is not supported or doesn't exist. Please check "
                f"the model name or use a different model.",
                header="=== MODEL ERROR ===",
            )
        )
        return ""

    except AIError as e:
        logger.error(f"AI service error: {str(e)}")
        print(
            format_bordered_text(
                f"An error occurred with the AI service: {str(e)}",
                header="=== AI SERVICE ERROR ===",
            )
        )
        return ""

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(
            format_bordered_text(f"An unexpected error occurred: {str(e)}", header="=== ERROR ===")
        )
        return ""


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
    conventional: bool = False,
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
        if not quiet:
            print_success("All changes staged.")

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
            print_header("SIMULATION MODE")
            logger.info("Using simulated files for test experience")
            if not quiet:
                print_info("Using simulated files for test experience.")
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
            if not quiet:
                print_warning("No staged files to commit. Use 'git add' to stage files first.")
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
        if not quiet:
            print_info("Formatting staged files...")
        any_formatted, formatted_exts = format_staged_files(stage_after_format=True)
        if any_formatted:
            logger.info(f"Formatted files with extensions: {', '.join(formatted_exts)}")
            if not quiet:
                print_success(f"Formatted files with extensions: {', '.join(formatted_exts)}")
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
            print_header("SIMULATION MODE")
            commit_message = send_to_llm(
                status=status,
                diff=diff,
                one_liner=one_liner,
                show_prompt=show_prompt,
                hint=hint,
                force=force,
                conventional=conventional,
            )
        else:
            print_header("TEST MODE")
            status = run_subprocess(["git", "status"])
            diff, truncated_files = get_staged_diff()

            if truncated_files:
                logger.warning(f"Large files detected and truncated: {', '.join(truncated_files)}")
                if not quiet:
                    print_warning(
                        f"Large files detected and truncated: {', '.join(truncated_files)}"
                    )
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
                conventional=conventional,
            )
    else:
        logger.debug("Checking for files to format...")

        # Only run formatting if enabled
        if config["use_formatting"] and not no_format:
            any_formatted, formatted_exts = format_staged_files(stage_after_format=True)
            if any_formatted:
                logger.info(f"Formatted files with extensions: {', '.join(formatted_exts)}")
                if not quiet:
                    print_success(f"Formatted files with extensions: {', '.join(formatted_exts)}")
            else:
                logger.debug("No files were formatted.")

        logger.info("Generating commit message...")
        if not quiet:
            print_info("Generating commit message...")
        status = run_subprocess(["git", "status"])
        diff, truncated_files = get_staged_diff()

        if truncated_files:
            logger.warning(f"Large files detected and truncated: {', '.join(truncated_files)}")
            if not quiet:
                print_warning(f"Large files detected and truncated: {', '.join(truncated_files)}")
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
            conventional=conventional,
        )

    if not commit_message:
        logger.error("Failed to generate commit message.")
        if not quiet:
            print_error("Failed to generate commit message.")
        return None

    # Use rich console to display the commit message
    console.print(Panel(commit_message, title="📝 Suggested Commit Message"))

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
            print_header("SIMULATION MODE")

            # Simulate the push prompt as well
            if force or testing:
                push = "y"
            else:
                prompt = "Would you like to simulate pushing these changes? (y/n)"
                push = click.prompt(prompt, type=str, default="y").strip().lower()

            if push and push[0] == "y":
                print_success("*** SIMULATION MODE: PUSH SIMULATED SUCCESSFULLY ***")
            else:
                print_info("*** SIMULATION MODE: PUSH SIMULATION ABORTED ***")
        else:
            print_header("TEST MODE")

            # Only show push prompt in test mode if not in simulation mode
            if force or testing:
                push = "y"
            else:
                prompt = "Do you want to push these changes? (y/n)"
                push = click.prompt(prompt, type=str, default="y").strip().lower()

            if push and push[0] == "y":
                print_success("*** TEST MODE: PUSH SIMULATION COMPLETED ***")
            else:
                print_info("*** TEST MODE: PUSH ABORTED ***")

        return commit_message

    # Real commit process
    commit_changes(commit_message)
    logger.info("Changes committed successfully.")
    if not quiet:
        print_success("Changes committed successfully.")

    if force or testing:
        push = "y"
    else:
        prompt = "Do you want to push these changes? (y/n)"
        push = click.prompt(prompt, type=str, default="y").strip().lower()

    if push and push[0] == "y":
        run_subprocess(["git", "push"])
        logger.info("Push complete.")
        if not quiet:
            print_success("Changes pushed successfully.")
    else:
        logger.info("Push aborted.")
        if not quiet:
            print_info("Push aborted.")

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
@click.option(
    "--conventional",
    "-c",
    is_flag=True,
    help="Generate commit messages using conventional commits format (type: description)",
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
    conventional: bool,
) -> None:
    """A CLI tool to generate commit messages using LLMs."""
    try:
        if quiet:
            # Suppress logging for non-error messages
            logging.getLogger().setLevel(logging.ERROR)
        elif verbose:
            # Enable debug logging
            logging.getLogger().setLevel(logging.DEBUG)

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
            conventional=conventional,
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
