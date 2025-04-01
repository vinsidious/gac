#!/usr/bin/env python3
"""Command-line interface for GAC."""

import logging
import os
import sys
from typing import Optional

import click

from gac.ai import is_ollama_available
from gac.git import commit_workflow
from gac.utils import print_error, print_info, print_success, setup_logging

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--log-level",
    default="WARNING",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Set log level (default: WARNING)",
)
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
    log_level: str,
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
    log_level = log_level.upper()
    log_level = logging.WARNING  # Default - only show warnings and errors
    if log_level == "DEBUG":
        log_level = logging.DEBUG
    elif log_level == "INFO":
        log_level = logging.INFO
    elif log_level == "WARNING":
        log_level = logging.WARNING
    elif log_level == "ERROR":
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
    """Generate a commit message using an LLM and commit your staged changes."""
    # Start with parent context values
    parent_ctx = ctx.parent.params

    # Create options dictionary using parent values but override with command-specific values
    # Use the value from this command if provided, otherwise use the parent value
    args = {
        "force": force if force is not None else parent_ctx.get("force", False),
        "add_all": add_all if add_all is not None else parent_ctx.get("add_all", False),
        "formatting": (
            not no_format if no_format is not None else not parent_ctx.get("no_format", False)
        ),
        "model": model if model is not None else parent_ctx.get("model"),
        "hint": hint if hint is not None else parent_ctx.get("hint", ""),
        "one_liner": one_liner if one_liner is not None else parent_ctx.get("one_liner", False),
        "show_prompt": (
            show_prompt if show_prompt is not None else parent_ctx.get("show_prompt", False)
        ),
        "show_prompt_full": (
            show_prompt_full
            if show_prompt_full is not None
            else parent_ctx.get("show_prompt_full", False)
        ),
        "quiet": parent_ctx.get("quiet", False),
        "no_spinner": no_spinner if no_spinner is not None else parent_ctx.get("no_spinner", False),
        "push": push if push is not None else parent_ctx.get("push", False),
    }

    # Run the commit workflow using the functional API
    result = commit_workflow(
        message=None,
        stage_all=args["add_all"],
        format_files=args["formatting"],
        model=args["model"],
        hint=args["hint"],
        one_liner=args["one_liner"],
        show_prompt=args["show_prompt"] or args["show_prompt_full"],
        require_confirmation=not args["force"],
        push=args["push"],
        quiet=args["quiet"],
    )

    # Check the result
    if not result["success"]:
        print_error(result["error"])
        sys.exit(1)

    print_success(f"Successfully committed changes with message: {result['message']}")
    if result.get("pushed"):
        print_success("Changes pushed to remote.")
    sys.exit(0)


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
