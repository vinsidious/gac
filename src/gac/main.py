"""Main entry point for the GAC application."""

import logging
import os
import sys

import click

from gac.workflow import CommitWorkflow

logger = logging.getLogger(__name__)


@click.command()
@click.option("--hint", type=str, help="Hint for the commit message")
@click.option("--formatter", type=str, help="Formatter to use: black, prettier, etc.")
@click.option("--no-formatting", is_flag=True, help="Skip formatting")
@click.option("--model", type=str, help="Override the model to use")
@click.option("-a", "--all", "add_all", is_flag=True, help="Stage all changes")
@click.option("-f", "--force", is_flag=True, help="Skip confirmation")
@click.option("--DEBUG", "log_level_debug", is_flag=True, help="Set log level to DEBUG")
@click.option("--INFO", "log_level_info", is_flag=True, help="Set log level to INFO")
@click.option("--WARNING", "log_level_warning", is_flag=True, help="Set log level to WARNING")
@click.option("--ERROR", "log_level_error", is_flag=True, help="Set log level to ERROR")
@click.option("-q", "--quiet", is_flag=True, help="Enable quiet mode (no prompts)")
@click.option("-t", "--test", is_flag=True, help="Test mode (no commit)")
def main(
    hint=None,
    formatter=None,
    no_formatting=False,
    model=None,
    add_all=False,
    force=False,
    log_level_debug=False,
    log_level_info=False,
    log_level_warning=False,
    log_level_error=False,
    quiet=False,
    test=False,
):
    """Run the main workflow for git-auto-commit."""
    try:
        # Determine log level from flags
        log_level = logging.WARNING  # Default - only show warnings and errors by default
        if log_level_debug:
            log_level = logging.DEBUG
        elif log_level_info:
            log_level = logging.INFO
        elif log_level_warning:
            log_level = logging.WARNING
        elif log_level_error:
            log_level = logging.ERROR

        # Configure logging
        setup_logging(log_level)

        # Validate incompatible flag combinations
        if quiet and (log_level_debug or log_level_info):
            raise click.UsageError("Cannot use both --quiet and logging level flags")

        if formatter and no_formatting:
            raise click.UsageError("Cannot use both --formatter and --no-formatting")

        # Check for multiple log level flags
        log_level_flags = sum([log_level_debug, log_level_info, log_level_warning, log_level_error])
        if log_level_flags > 1:
            raise click.UsageError("Only one log level flag can be used at a time")

        # Use formatter if specified, otherwise use formatting unless no_formatting is True
        formatting = bool(formatter or not no_formatting)

        # Create and run the workflow
        workflow = CommitWorkflow(
            hint=hint,
            formatter=formatter,
            verbose=(log_level == logging.DEBUG),  # For backward compatibility
            quiet=quiet,
            test=test,
            formatting=formatting,
            add_all=add_all,
            force=force,
            model_override=model,
        )

        return workflow.run()

    except Exception as err:
        if log_level == logging.DEBUG:
            logger.exception("Error occurred:")
        else:
            logger.error(f"Error: {err}")
        sys.exit(1)


def setup_logging(log_level=logging.WARNING):
    """Configure logging for the application.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR)
    """
    # Check for environment variable override
    log_level_env = os.environ.get("GAC_LOG_LEVEL")
    if log_level_env:
        log_level_env = log_level_env.upper()
        if log_level_env == "DEBUG":
            log_level = logging.DEBUG
        elif log_level_env == "INFO":
            log_level = logging.INFO
        elif log_level_env == "WARNING":
            log_level = logging.WARNING
        elif log_level_env == "ERROR":
            log_level = logging.ERROR
        else:
            logger.warning(
                f"Unknown GAC_LOG_LEVEL: {log_level_env}, using {logging.getLevelName(log_level)}"
            )

    if log_level == logging.DEBUG:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(levelname)s: %(message)s",
        )

    # Suppress excessive logs from libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


if __name__ == "__main__":
    main()
