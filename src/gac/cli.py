#!/usr/bin/env python3
"""Command-line interface for GAC."""

import logging
import os
import sys
from typing import Optional

import click

from gac.ai import is_ollama_available
from gac.git import commit_changes, run_git_command
from gac.utils import print_error, print_info, print_success, setup_logging

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("--DEBUG", "log_level_debug", is_flag=True, help="Set log level to DEBUG")
@click.option("--INFO", "log_level_info", is_flag=True, help="Set log level to INFO")
@click.option("--WARNING", "log_level_warning", is_flag=True, help="Set log level to WARNING")
@click.option("--ERROR", "log_level_error", is_flag=True, help="Set log level to ERROR")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
# Add commit options to main command
@click.option("--force", "-f", is_flag=True, help="Skip all confirmation prompts")
@click.option("--add-all", "-a", is_flag=True, help="Stage all changes before committing")
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
@click.option("--hint", "-h", default="", help="Additional context to include in the prompt")
@click.option("--push", "-p", is_flag=True, help="Push changes to remote after committing")
@click.pass_context
def cli(
    ctx,
    log_level_debug: bool,
    log_level_info: bool,
    log_level_warning: bool,
    log_level_error: bool,
    quiet: bool,
    force: bool = False,
    add_all: bool = False,
    no_format: bool = False,
    model: Optional[str] = None,
    one_liner: bool = False,
    show_prompt: bool = False,
    show_prompt_full: bool = False,
    hint: str = "",
    no_spinner: bool = False,
    push: bool = False,
) -> None:
    """Git Auto Commit - Generate commit messages with AI."""
    # Set up context for all commands
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet

    # Store commit options in context
    ctx.obj["force"] = force
    ctx.obj["add_all"] = add_all
    ctx.obj["no_format"] = no_format
    ctx.obj["model"] = model
    ctx.obj["one_liner"] = one_liner
    ctx.obj["show_prompt"] = show_prompt
    ctx.obj["show_prompt_full"] = show_prompt_full
    ctx.obj["hint"] = hint
    ctx.obj["no_spinner"] = no_spinner
    ctx.obj["push"] = push

    # Determine log level from flags
    log_level = logging.WARNING  # Default - only show warnings and errors
    if log_level_debug:
        log_level = logging.DEBUG
    elif log_level_info:
        log_level = logging.INFO
    elif log_level_warning:
        log_level = logging.WARNING
    elif log_level_error:
        log_level = logging.ERROR

    setup_logging(log_level, quiet=quiet, force=True)

    # If no subcommand is specified, invoke commit by default
    if ctx.invoked_subcommand is None:
        # Pass the flags explicitly to the commit function
        ctx.invoke(
            commit,
            force=force,
            add_all=add_all,
            no_format=no_format,
            model=model,
            one_liner=one_liner,
            show_prompt=show_prompt,
            show_prompt_full=show_prompt_full,
            hint=hint,
            no_spinner=no_spinner,
            push=push,
        )


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Skip all confirmation prompts")
@click.option("--add-all", "-a", is_flag=True, help="Stage all changes before committing")
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
@click.option("--hint", "-h", default="", help="Additional context to include in the prompt")
@click.option("--push", "-p", is_flag=True, help="Push changes to remote after committing")
@click.pass_context
def commit(
    ctx,
    force: bool = None,
    add_all: bool = None,
    no_format: bool = None,
    model: Optional[str] = None,
    one_liner: bool = None,
    show_prompt: bool = None,
    show_prompt_full: bool = None,
    hint: str = None,
    no_spinner: bool = None,
    push: bool = None,
) -> None:
    """Generate a commit message and commit changes."""
    quiet = ctx.obj["quiet"]

    # Use values from context if not provided directly to the command
    force = force if force is not None else ctx.obj.get("force", False)
    add_all = add_all if add_all is not None else ctx.obj.get("add_all", False)
    no_format = no_format if no_format is not None else ctx.obj.get("no_format", False)
    model = model if model is not None else ctx.obj.get("model")
    one_liner = one_liner if one_liner is not None else ctx.obj.get("one_liner", False)
    show_prompt = show_prompt if show_prompt is not None else ctx.obj.get("show_prompt", False)
    show_prompt_full = (
        show_prompt_full if show_prompt_full is not None else ctx.obj.get("show_prompt_full", False)
    )
    hint = hint if hint is not None else ctx.obj.get("hint", "")
    no_spinner = no_spinner if no_spinner is not None else ctx.obj.get("no_spinner", False)
    push = push if push is not None else ctx.obj.get("push", False)

    # Debug logging for flags
    logger.debug(f"CLI commit function - add_all: {add_all}, force: {force}, push: {push}")
    logger.debug(f"CLI commit function - ctx.obj: {ctx.obj}")

    try:
        commit_message = commit_changes(
            force=force,
            add_all=add_all,
            formatting=not no_format,
            model=model,
            one_liner=one_liner,
            show_prompt=show_prompt,
            show_prompt_full=show_prompt_full,
            hint=hint,
            quiet=quiet,
            no_spinner=no_spinner,
            push=push,
        )

        if not commit_message and not quiet:
            if "Commit cancelled" in run_git_command(["log", "-1"], silent=True):
                sys.exit(0)
            logger.error("Failed to generate or apply commit")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def models(ctx) -> None:
    """List available local Ollama models."""
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

        print_info("\nUse with: gac commit --model ollama:MODEL_NAME")
    except Exception as e:
        print_error(f"Error listing Ollama models: {e}")
        print_info("Make sure Ollama is installed and running.")


@cli.command()
@click.pass_context
def config(ctx) -> None:
    """Run the interactive configuration wizard."""
    from gac.config import run_config_wizard

    result = run_config_wizard()
    if result:
        # Save configuration to environment variables
        os.environ["GAC_MODEL"] = result["model"]
        os.environ["GAC_USE_FORMATTING"] = str(result["use_formatting"]).lower()
        print_success("Configuration saved successfully!")


# For backward compatibility with existing scripts
def main():
    """Entry point for setup.py console_scripts."""
    cli(obj={})


if __name__ == "__main__":
    cli(obj={})
