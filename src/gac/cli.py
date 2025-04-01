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


@click.group()
@click.option("--DEBUG", "log_level_debug", is_flag=True, help="Set log level to DEBUG")
@click.option("--INFO", "log_level_info", is_flag=True, help="Set log level to INFO")
@click.option("--WARNING", "log_level_warning", is_flag=True, help="Set log level to WARNING")
@click.option("--ERROR", "log_level_error", is_flag=True, help="Set log level to ERROR")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.pass_context
def cli(
    ctx,
    log_level_debug: bool,
    log_level_info: bool,
    log_level_warning: bool,
    log_level_error: bool,
    quiet: bool,
) -> None:
    """Git Auto Commit - Generate commit messages with AI."""
    # Set up context for all commands
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet

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
@click.option(
    "--no-spinner",
    is_flag=True,
    help="Disable progress spinner during API calls",
)
@click.option("--push", "-p", is_flag=True, help="Push changes to remote after committing")
@click.pass_context
def commit(
    ctx,
    force: bool,
    add_all: bool,
    no_format: bool,
    model: Optional[str],
    one_liner: bool,
    show_prompt: bool,
    show_prompt_full: bool,
    hint: str,
    no_spinner: bool,
    push: bool,
) -> None:
    """Generate a commit message and commit changes."""
    quiet = ctx.obj["quiet"]

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
