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
from gac.prompts import build_prompt, clean_commit_message, create_abbreviated_prompt
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
        "test (testing), build (build system), ci (CI config), "
        "chore (other changes), deps (dependency updates), "
        "revert (revert previous changes), wip (work in progress), "
        "security (security fixes), i18n (internationalization), "
        "a11y (accessibility), dx (developer experience), "
        "ui (user interface), ux (user experience), "
        "data (data related changes), config (configuration changes). "
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
            "Failed to connect to the AI service. Please check your internet "
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


if __name__ == "__main__":
    cli()
