#!/usr/bin/env python3
"""Main module for gac."""

import logging
import os
import subprocess
import sys
from typing import Optional

import click

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
from gac.cache import Cache
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
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
    run_subprocess,
)

logger = logging.getLogger(__name__)

# Cache for core operations
core_cache = Cache()


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
        The formatted prompt string
    """
    prompt = [
        "Write a concise and meaningful git commit message based on the staged changes "
        "shown below.",
    ]

    if one_liner:
        prompt.append(
            "\nFormat it as a single line (50-72 characters if possible). "
            "If applicable, still use conventional commit prefixes like feat/fix/docs/etc., "
            "but keep everything to a single line with no bullet points."
        )
    else:
        prompt.append(
            "\nFormat it with a concise summary line (50-72 characters) followed by a "
            "more detailed explanation with multiple bullet points highlighting the "
            "specific changes made. Order the bullet points from most important to least important."
        )

    if conventional:
        prompt.append(
            "\nIMPORTANT: EVERY commit message MUST start with a conventional commit prefix. "
            "This is a HARD REQUIREMENT. Choose from:"
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
            "\n\nYOU MUST choose the most appropriate type based on the changes. "
            "If you CANNOT determine a type, use 'chore'. "
            "THE PREFIX IS MANDATORY - NO EXCEPTIONS."
        )

    if hint:
        prompt.append(f"\nPlease consider this context from the user: {hint}")

    prompt.append(
        "\nDo not include any explanation or preamble like 'Here's a commit message', etc."
    )
    prompt.append("Just output the commit message directly.")
    prompt.append("\n\nCurrent git status:")
    prompt.append("<git-status>")
    prompt.append(status)
    prompt.append("</git-status>")
    prompt.append("\nChanges to be committed:")
    prompt.append("<git-diff>")
    prompt.append(diff)
    prompt.append("</git-diff>")

    return "\n".join(prompt)


def clean_commit_message(message: str) -> str:
    """
    Clean the commit message to ensure it doesn't contain triple backticks or XML tags
    at the beginning or end, or around individual bullet points.

    Args:
        message: The commit message to clean

    Returns:
        The cleaned commit message
    """
    # Conventional commit types
    valid_types = [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
    ]

    # Remove triple backticks at the beginning
    if message.startswith("```"):
        message = message[3:].lstrip()

    # Remove language identifier if present (like ```python)
    if message.startswith("```"):
        first_newline = message.find("\n")
        if first_newline > 0:
            message = message[first_newline:].lstrip()

    # Remove triple backticks at the end
    if message.endswith("```"):
        message = message[:-3].rstrip()

    # Remove git status XML tags if present
    if message.startswith("<git-status>"):
        end_tag_pos = message.find("</git-status>")
        if end_tag_pos > 0:
            message = message[end_tag_pos + len("</git-status>") :].lstrip()

    # Remove git diff XML tags if present
    if message.startswith("<git-diff>"):
        end_tag_pos = message.find("</git-diff>")
        if end_tag_pos > 0:
            message = message[end_tag_pos + len("</git-diff>") :].lstrip()

    # Split into lines
    lines = message.split("\n")

    # Enforce conventional commit prefix
    first_line = lines[0].strip()

    # Check if the first line starts with a valid type
    type_match = next((t for t in valid_types if first_line.startswith(f"{t}:")), None)

    if not type_match:
        # If no valid type, default to 'chore'
        first_line = f"chore: {first_line}"
        lines[0] = first_line

    # Clean individual bullet points
    for i, line in enumerate(lines):
        # Check if this is a bullet point with backticks
        if line.strip().startswith("- "):
            # Remove backticks at the beginning of the bullet content
            content = line.strip()[2:].lstrip()
            if content.startswith("```"):
                content = content[3:].lstrip()

            # Remove backticks at the end of the bullet content
            if content.endswith("```"):
                content = content[:-3].rstrip()

            # Remove XML tags from bullet points
            if content.startswith("<git-"):
                for tag in ["<git-status>", "<git-diff>"]:
                    if content.startswith(tag):
                        end_tag = tag.replace("<", "</")
                        end_pos = content.find(end_tag)
                        if end_pos > 0:
                            content = content[end_pos + len(end_tag) :].lstrip()

            # Reconstruct the bullet point
            lines[i] = "- " + content

    return "\n".join(lines)


def send_to_llm(
    status: str,
    diff: str,
    one_liner: bool = False,
    show_prompt: bool = False,
    show_prompt_full: bool = False,
    hint: str = "",
    force: bool = False,
    conventional: bool = False,
    cache_skip: bool = False,
    show_spinner: bool = True,
) -> str:
    """
    Send the git status and staged diff to an LLM for summarization.

    Args:
        status: Output of git status
        diff: Output of git diff --staged
        one_liner: If True, request a single-line commit message
        show_prompt: If True, display an abbreviated version of the prompt
        show_prompt_full: If True, display the complete prompt with full diff
        hint: Optional context to include in the prompt (like "JIRA-123")
        force: If True, skip confirmation prompts
        conventional: If True, request a conventional commit format message
        cache_skip: If True, bypass cache and force a new API call
        show_spinner: If True, display a spinner during API calls

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

    # Check if token count exceeds the warning limit
    warning_limit_tokens = config["warning_limit_input_tokens"]
    if token_count > warning_limit_tokens:
        logger.warning(
            f"Warning: Prompt exceeds warning limit ({token_count} > {warning_limit_tokens})"
        )
        if not force:
            prompt_msg = (
                f"The prompt is {token_count:,} tokens, which exceeds the warning limit "
                f"of {warning_limit_tokens:,}. Continue anyway?"
            )
            if not click.confirm(prompt_msg, default=False):
                logger.info("Operation cancelled by user")
                return ""

    # Show prompt if requested
    if show_prompt_full:
        print_info("🤖 Crafting LLM Prompt")
        print(prompt)
    elif show_prompt:
        print_info("🤖 Crafting LLM Prompt")
        abbreviated_prompt = create_abbreviated_prompt(prompt)
        print(abbreviated_prompt)

    # Get project description and include it in context if available
    project_description = get_project_description()
    system = (
        "You are a helpful assistant that writes clear, concise git commit messages. "
        "EVERY commit message MUST start with a conventional commit prefix. "
        "Conventional commit types are: "
        "feat (new feature), fix (bug fix), docs (documentation), "
        "style (formatting), refactor (code changes), perf (performance), "
        "test (testing), build (build system), ci (CI config), chore (other changes). "
        "If you cannot determine a type, use 'chore'. "
        "Only output the commit message, nothing else. "
        "NEVER include triple backticks (```) or XML tags (like <git-status> or <git-diff>) "
        "at the beginning or end of your commit message. "
        "When creating bullet points, always list the most important changes first, "
        "followed by less important ones in descending order of significance."
    )

    # Add project description to system message if available
    if project_description:
        system = (
            "You are a helpful assistant that writes clear, concise git commit messages "
            f"for the following project: '{project_description}'. "
            "EVERY commit message MUST start with a conventional commit prefix. "
            "Conventional commit types are: "
            "feat (new feature), fix (bug fix), docs (documentation), "
            "style (formatting), refactor (code changes), perf (performance), "
            "test (testing), build (build system), ci (CI config), chore (other changes). "
            "If you cannot determine a type, use 'chore'. "
            "Only output the commit message, nothing else. "
            "NEVER include triple backticks (```) or XML tags (like <git-status> or <git-diff>) "
            "at the beginning or end of your commit message. "
            "When creating bullet points, always list the most important changes first, "
            "followed by less important ones in descending order of significance."
        )

    messages = [{"role": "user", "content": prompt}]

    try:
        response = chat(
            messages=messages,
            model=model,
            temperature=0.7,
            system=system,
            test_mode=False,
            cache_skip=cache_skip,
            show_spinner=show_spinner,
            one_liner=one_liner,
        )

        response_token_count = count_tokens(response, model)
        logger.info(f"Response token count: {response_token_count:,}")

        # Clean the response to ensure no triple backticks
        cleaned_response = clean_commit_message(response)
        return cleaned_response

    except APIConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        print(
            f"Failed to connect to the AI service. Please check your internet "
            "connection and try again."
        )
        return ""

    except APITimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        print("The AI service took too long to respond. Please try again later.")
        return ""

    except APIRateLimitError as e:
        logger.error(f"Rate limit error: {str(e)}")
        print("Rate limit exceeded for the AI service. Please wait a few minutes and try again.")
        return ""

    except APIAuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        provider = model.split(":")[0] if ":" in model else "your AI"
        print(
            f"Authentication failed for {provider} API. Please check your API key and ensure "
            f"it's properly set in your environment variables."
        )
        return ""

    except APIUnsupportedModelError as e:
        logger.error(f"Model error: {str(e)}")
        print(
            f"The model '{model}' is not supported or doesn't exist. Please check "
            f"the model name or use a different model."
        )
        return ""

    except AIError as e:
        logger.error(f"AI service error: {str(e)}")
        print(f"An error occurred with the AI service: {str(e)}")
        return ""

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")
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
    show_prompt_full: bool = False,
    test_with_real_diff: bool = False,
    testing: bool = False,  # Used only during test suite runs
    hint: str = "",
    conventional: bool = False,
    no_cache: bool = False,
    clear_cache: bool = False,
    no_spinner: bool = False,
):
    """Generate and apply a commit message."""
    config = get_config()

    # Set logging level
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    # Clear cache if requested
    if clear_cache:
        import shutil
        from pathlib import Path

        from gac.cache import DEFAULT_CACHE_DIR

        cache_dir = Path(DEFAULT_CACHE_DIR)
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            logger.info("Cache cleared successfully")
            if not quiet:
                print_success("Cache cleared successfully.")

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
            try:
                run_subprocess(["git", "stash", "--keep-index", "-q"])  # Keep index, quiet mode
                restore_unstaged = True
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to stash unstaged changes: {e}")
                logger.info("Continuing without stashing unstaged changes")
                restore_unstaged = False

    # Format only the staged changes
    if not no_format and not testing:
        logger.info("Formatting staged files...")
        if not quiet:
            print_info("Formatting staged files...")
        any_formatted, formatted_exts = format_staged_files(stage_after_format=True)
        if any_formatted:
            logger.info(f"Formatted files with extensions: {', '.join(formatted_exts)}")
            if not quiet:
                for ext in formatted_exts:
                    if ext == ".py":
                        py_files = [f for f in staged_files if f.endswith(ext)]
                        print_success(f"✅ Formatted {len(py_files)} Python files with Black")
                    elif ext == ".js" or ext == ".ts":
                        js_files = [f for f in staged_files if f.endswith(ext)]
                        print_success(
                            f"✅ Formatted {len(js_files)} "
                            "JavaScript/TypeScript files with Prettier"
                        )
                    elif ext == ".md":
                        md_files = [f for f in staged_files if f.endswith(ext)]
                        print_success(f"✅ Formatted {len(md_files)} Markdown files with Prettier")
                    else:
                        print_success(f"✅ Formatted files with extension {ext}")
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
                show_prompt_full=show_prompt_full,
                hint=hint,
                force=force,
                conventional=conventional,
                cache_skip=no_cache,
                show_spinner=not no_spinner,
            )
        else:
            print_header("TEST MODE")
            status = run_subprocess(["git", "status"])
            diff, truncated_files = get_staged_diff()

            if truncated_files:
                logger.warning(f"Large files detected and truncated: {', '.join(truncated_files)}")
                if not quiet:
                    print_warning("Large files detected and truncated:")
                    for truncated_file in truncated_files:
                        print_warning(f"  - {truncated_file}")
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
                show_prompt_full=show_prompt_full,
                hint=hint,
                force=force,
                conventional=conventional,
                cache_skip=no_cache,
                show_spinner=not no_spinner,
            )
    else:
        logger.debug("Checking for files to format...")

        # Only run formatting if enabled
        if config["use_formatting"] and not no_format:
            any_formatted, formatted_exts = format_staged_files(stage_after_format=True)
            if any_formatted:
                logger.info(f"Formatted files with extensions: {', '.join(formatted_exts)}")
                if not quiet:
                    for ext in formatted_exts:
                        if ext == ".py":
                            py_files = [f for f in staged_files if f.endswith(ext)]
                            print_success(f"✅ Formatted {len(py_files)} Python files with Black")
                        elif ext == ".js" or ext == ".ts":
                            js_files = [f for f in staged_files if f.endswith(ext)]
                            print_success(
                                f"✅ Formatted {len(js_files)} "
                                "JavaScript/TypeScript files with Prettier"
                            )
                        elif ext == ".md":
                            md_files = [f for f in staged_files if f.endswith(ext)]
                            print_success(
                                f"✅ Formatted {len(md_files)} Markdown files with Prettier"
                            )
                        else:
                            print_success(f"✅ Formatted files with extension {ext}")
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
                print_warning("Large files detected and truncated:")
                for truncated_file in truncated_files:
                    print_warning(f"  - {truncated_file}")
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
            show_prompt_full=show_prompt_full,
            hint=hint,
            force=force,
            conventional=conventional,
            cache_skip=no_cache,
            show_spinner=not no_spinner,
        )

    if not commit_message:
        logger.error("Failed to generate commit message.")
        if not quiet:
            print_error("Failed to generate commit message.")
        return None

    # Use rich console to display the commit message without borders
    print(commit_message)
    print()  # Add an extra blank line

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
@click.option("--test", "-t", is_flag=True, help="Run in test mode without making git commits")
@click.option("--force", "-f", is_flag=True, help="Skip all confirmation prompts")
@click.option("--add-all", "-a", is_flag=True, help="Stage all changes before committing")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--no-format", is_flag=True, help="Skip formatting of staged files")
@click.option(
    "--model",
    "-m",
    help="Override the default model (format: 'provider:model_name', e.g. 'ollama:llama3.2')",
)
@click.option("--one-liner", "-o", is_flag=True, help="Generate a single-line commit message")
@click.option(
    "--show-prompt",
    "-s",
    is_flag=True,
    help="Show an abbreviated version of the prompt sent to the LLM",
)
@click.option(
    "--show-prompt-full",
    is_flag=True,
    help="Show the complete prompt sent to the LLM, including full diff",
)
@click.option("--test-with-diff", is_flag=True, help="Test with real staged changes (if any)")
@click.option("--hint", "-h", default="", help="Additional context to include in the prompt")
@click.option(
    "--conventional",
    "-c",
    is_flag=True,
    help="Generate a conventional commit format message",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Skip cache and force fresh API calls",
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="Clear all cached data before running",
)
@click.option(
    "--no-spinner",
    is_flag=True,
    help="Disable progress spinner during API calls",
)
@click.option(
    "--local-models",
    is_flag=True,
    help="List available local Ollama models and exit",
)
@click.option(
    "--config-wizard",
    is_flag=True,
    help="Run the interactive configuration wizard",
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
    show_prompt_full: bool,
    test_with_diff: bool,
    hint: str,
    conventional: bool,
    no_cache: bool,
    clear_cache: bool,
    no_spinner: bool,
    local_models: bool,
    config_wizard: bool,
) -> None:
    """Git Auto Commit CLI."""
    # Configuration wizard takes precedence
    if config_wizard:
        from gac.config import run_config_wizard

        config = run_config_wizard()
        if config:
            # Save configuration to environment variables
            os.environ["GAC_MODEL"] = config["model"]
            os.environ["GAC_USE_FORMATTING"] = str(config["use_formatting"]).lower()
            print("Configuration saved successfully!")
        return

    # Rest of the existing CLI logic remains the same
    if local_models:
        list_local_models()
        return

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
            show_prompt_full=show_prompt_full,
            test_with_real_diff=test_with_diff,
            hint=hint,
            conventional=conventional,
            no_cache=no_cache,
            clear_cache=clear_cache,
            no_spinner=no_spinner,
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def list_local_models() -> None:
    """List available local Ollama models."""
    from gac.ai_utils import is_ollama_available
    from gac.utils import print_error, print_info, print_success

    print_info("Checking for local Ollama models...")

    if not is_ollama_available():
        print_error(
            "Ollama is not available. Install from https://ollama.com and make sure it's running."
        )
        print_info("After installing, run 'ollama pull llama3.2' to download a model.")
        return

    try:
        import ollama

        models = ollama.list().get("models", [])

        if not models:
            print_info("No Ollama models found. Run 'ollama pull llama3.2' to download a model.")
            return

        print_success(f"Found {len(models)} Ollama models:")
        for model in models:
            name = model.get("name", "unknown")
            size = model.get("size", 0) // (1024 * 1024)  # Convert to MB
            print_info(f"  - {name} ({size} MB)")

        print_info("\nUse with: gac --model ollama:MODEL_NAME")
    except Exception as e:
        print_error(f"Error listing Ollama models: {e}")
        print_info("Make sure Ollama is installed and running.")


def create_abbreviated_prompt(prompt: str, max_diff_lines: int = 50) -> str:
    """
    Create an abbreviated version of the prompt by limiting the diff lines.

    Args:
        prompt: The original full prompt
        max_diff_lines: Maximum number of diff lines to include

    Returns:
        Abbreviated prompt with a note about hidden lines
    """
    # Find the start and end of the diff section
    changes_marker = "Changes to be committed:"
    changes_idx = prompt.find(changes_marker)

    # If we can't find the marker, return the original prompt
    if changes_idx == -1:
        return prompt

    # Find the start of the git diff XML tag
    code_start_tag = "<git-diff>"
    code_start_idx = prompt.find(code_start_tag, changes_idx)
    if code_start_idx == -1:
        return prompt

    # Find the end of the git diff XML tag
    code_end_tag = "</git-diff>"
    code_end_idx = prompt.find(code_end_tag, code_start_idx + len(code_start_tag))
    if code_end_idx == -1:
        return prompt

    # Extract parts of the prompt
    before_diff = prompt[: code_start_idx + len(code_start_tag)]  # Include the opening tag
    diff_content = prompt[code_start_idx + len(code_start_tag) : code_end_idx]
    after_diff = prompt[code_end_idx:]  # Include the closing tag and anything after

    # Split the diff into lines
    diff_lines = diff_content.split("\n")
    total_lines = len(diff_lines)

    # If the diff is already short enough, return the original prompt
    if total_lines <= max_diff_lines:
        return prompt

    # Extract the beginning and end of the diff
    half_max = max_diff_lines // 2
    first_half = diff_lines[:half_max]
    second_half = diff_lines[-half_max:]

    # Calculate how many lines we're hiding
    hidden_lines = total_lines - len(first_half) - len(second_half)

    # Create the hidden lines message
    hidden_message = (
        f"\n\n... {hidden_lines} lines hidden ...\n"
        f"Use --show-prompt-full to see the complete diff\n\n"
    )

    # Create the abbreviated diff
    abbreviated_diff = "\n".join(first_half) + hidden_message + "\n".join(second_half)

    # Reconstruct the prompt
    return before_diff + abbreviated_diff + after_diff


if __name__ == "__main__":
    cli()
