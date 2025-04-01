#!/usr/bin/env python3
"""Workflow module for GAC."""

import logging
from typing import Optional

from gac.commit_manager import CommitManager
from gac.errors import GACError, convert_exception, handle_error
from gac.formatting_controller import FormattingController
from gac.git_operations import GitOperationsManager

logger = logging.getLogger(__name__)


# Function to maintain compatibility with tests
def send_to_llm(prompt, model=None, api_key=None, max_tokens_to_sample=4096):
    """
    Send prompt to LLM (compatibility function for tests).

    Args:
        prompt: Prompt to send to model
        model: Model to use
        api_key: API key to use
        max_tokens_to_sample: Maximum tokens to sample in response

    Returns:
        Model response text
    """
    # Create a commit manager and use it to send the prompt
    commit_manager = CommitManager(
        quiet=True,
        model_override=model,
    )

    # Treat prompt as diff for compatibility with updated function
    return commit_manager._send_to_llm("", prompt, False, "", False)


class CommitWorkflow:
    """Class that manages the Git commit workflow."""

    def __init__(
        self,
        force: bool = False,
        add_all: bool = False,
        no_format: bool = False,
        quiet: bool = False,
        verbose: bool = False,
        model: Optional[str] = None,
        one_liner: bool = False,
        show_prompt: bool = False,
        show_prompt_full: bool = False,
        hint: str = "",
        conventional: bool = False,
        no_spinner: bool = False,
        formatter: str = None,
        formatting: bool = True,
        model_override: str = None,
        push: bool = False,
    ):
        """
        Initialize the CommitWorkflow.

        Args:
            force: Skip all confirmation prompts
            add_all: Stage all changes before committing
            no_format: Skip formatting of staged files
            quiet: Suppress non-error output
            verbose: Enable verbose logging (sets to DEBUG level)
            model: Override the default model
            one_liner: Generate a single-line commit message
            show_prompt: Show an abbreviated version of the prompt
            show_prompt_full: Show the complete prompt including full diff
            hint: Additional context to include in the prompt
            conventional: Generate a conventional commit format message
            no_spinner: Disable progress spinner during API calls
            formatter: Specific formatter to use
            formatting: Whether to perform code formatting
            model_override: Override the model to use
            push: Push changes to remote after committing
        """
        self.force = force
        self.add_all = add_all
        self.quiet = quiet
        self.verbose = verbose
        self.hint = hint
        self.formatter = formatter
        # Prefer no_format for backwards compatibility
        self.formatting = formatting and not no_format
        self.model_override = model_override or model
        self.push = push

        # If verbose is set, ensure logging level is DEBUG
        if self.verbose:
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            logger.debug("Verbose mode: setting log level to DEBUG")

        # Initialize components
        self.git_manager = GitOperationsManager(quiet=quiet)
        self.formatting_controller = FormattingController()
        self.commit_manager = CommitManager(
            quiet=quiet,
            model_override=self.model_override,
            one_liner=one_liner,
            show_prompt=show_prompt,
            show_prompt_full=show_prompt_full,
            hint=hint,
            conventional=conventional,
            no_spinner=no_spinner,
        )

    def run(self):
        """Execute the full commit workflow."""
        try:
            # Ensure we're in a git repository
            if not self.git_manager.ensure_git_directory():
                return None

            # Stage all files if requested
            if self.add_all:
                self.git_manager.stage_all_files()

            # Get staged files and diff
            staged_files = self.git_manager.get_staged_files()
            if not staged_files:
                logger.error("No staged changes found. Stage your changes with git add first.")
                return None

            # Format staged files if needed
            if self.formatting:
                self._format_staged_files(staged_files)

            # Get the diff of staged changes
            diff = self.git_manager.get_staged_diff()
            if not diff:
                logger.error("No diff found for staged changes.")
                return None

            # Get git status
            status = self.git_manager.get_status()

            # Generate commit message
            commit_message = self.commit_manager.generate_message(status, diff)
            if not commit_message:
                logger.error("Failed to generate commit message.")
                return None

            # Always display the commit message
            if not self.quiet:
                print("\nGenerated commit message:")
                print("------------------------")
                print(commit_message)
                print("------------------------")

            # If force mode is not enabled, prompt for confirmation
            if not self.force and not self.quiet:
                confirm = input("\nProceed with this commit message? (y/n): ").strip().lower()
                if confirm == "n":
                    print("Commit canceled.")
                    return None

            # Execute the commit
            success = self.git_manager.commit_changes(commit_message)
            if not success:
                handle_error(GACError("Failed to commit changes"), quiet=self.quiet)
                return None

            # Push changes if requested
            if self.push and success:
                push_success = self.git_manager.push_changes()
                if not push_success:
                    handle_error(
                        GACError("Failed to push changes"), quiet=self.quiet, exit_program=False
                    )

            return commit_message

        except Exception as e:
            error = convert_exception(e, GACError, "An error occurred during workflow execution")
            handle_error(error, quiet=self.quiet)
            return None

    def _format_staged_files(self, staged_files):
        """
        Format the staged files and re-stage them.

        Args:
            staged_files: List of staged file paths

        Returns:
            A dictionary of formatted files by formatter
        """
        if not self.quiet:
            print("ℹ️ Formatting staged files...")
        elif logging.getLogger().getEffectiveLevel() <= logging.INFO:
            logger.info("ℹ️ Formatting staged files...")

        formatted_files = self.formatting_controller.format_staged_files(staged_files, self.quiet)

        if not self.quiet:
            print("✅ Formatting complete")
        elif logging.getLogger().getEffectiveLevel() <= logging.INFO:
            logger.info("✅ Formatting complete")

        # Re-stage formatted files
        if formatted_files:
            # Collect all formatted file paths
            files_to_stage = []
            for formatter, files in formatted_files.items():
                files_to_stage.extend(files)

            if files_to_stage:
                if not self.quiet:
                    print("ℹ️ Re-staging formatted files...")

                # Re-stage the formatted files
                self.git_manager.stage_files(files_to_stage)

                if not self.quiet:
                    print("✅ Formatted files re-staged")

        return formatted_files
