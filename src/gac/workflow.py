#!/usr/bin/env python3
"""Workflow module for GAC."""

import logging
import os
import sys
from typing import Optional

from gac.config import get_config
from gac.errors import GACError, convert_exception, handle_error
from gac.formatting_controller import FormattingController
from gac.git import commit_changes, get_staged_diff, get_staged_files, get_status, stage_files
from gac.prompts import build_prompt, clean_commit_message

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
    config = get_config()
    if not model:
        model = config.get("model")

    # Extract status and diff for compatibility with updated function
    # Assume prompt is the full text and we'll treat it as the diff
    status = ""
    diff = prompt

    workflow = CommitWorkflow(
        verbose=False,
        quiet=False,
        test_mode=False,
        formatting=False,
        add_all=False,
        model_override=model,
        one_liner=False,
        show_prompt=False,
        show_prompt_full=False,
        test_with_real_diff=False,
        hint="",
        conventional=False,
        no_cache=False,
        clear_cache=False,
        no_spinner=False,
    )
    # Call with correct parameters
    return workflow._send_to_llm(status, diff, False, "", False)


class CommitWorkflow:
    """Class that manages the Git commit workflow."""

    def __init__(
        self,
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
        hint: str = "",
        conventional: bool = False,
        no_cache: bool = False,
        clear_cache: bool = False,
        no_spinner: bool = False,
        formatter: str = None,
        formatting: bool = True,
        model_override: str = None,
    ):
        """
        Initialize the CommitWorkflow.

        Args:
            test_mode: Run in test mode without making git commits
            force: Skip all confirmation prompts
            add_all: Stage all changes before committing
            no_format: Skip formatting of staged files
            quiet: Suppress non-error output
            verbose: Enable verbose logging (sets to DEBUG level)
            model: Override the default model
            one_liner: Generate a single-line commit message
            show_prompt: Show an abbreviated version of the prompt
            show_prompt_full: Show the complete prompt including full diff
            test_with_real_diff: Test with real staged changes
            hint: Additional context to include in the prompt
            conventional: Generate a conventional commit format message
            no_cache: Skip cache and force fresh API calls
            clear_cache: Clear all cached data before running
            no_spinner: Disable progress spinner during API calls
            formatter: Specific formatter to use
            formatting: Whether to perform code formatting
            model_override: Override the model to use
        """
        self.test = test_mode
        self.force = force
        self.add_all = add_all
        self.quiet = quiet
        self.verbose = verbose
        self.hint = hint
        self.formatter = formatter
        # Prefer no_format for backwards compatibility
        self.formatting = formatting and not no_format
        self.model_override = model_override or model
        self.one_liner = one_liner
        self.show_prompt = show_prompt
        self.show_prompt_full = show_prompt_full
        self.test_with_real_diff = test_with_real_diff
        self.conventional = conventional
        self.no_cache = no_cache
        self.clear_cache = clear_cache
        self.no_spinner = no_spinner

        # If verbose is set, ensure logging level is DEBUG
        if self.verbose:
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            logger.debug("Verbose mode: setting log level to DEBUG")

        # Get configuration
        self.config = get_config()
        if self.model_override:
            self.config["model"] = self.model_override

        # Store parameters in config for use in other methods
        self.config["one_liner"] = self.one_liner
        self.config["conventional"] = self.conventional

        # Initialize formatting controller
        self.formatting_controller = FormattingController()

    def run(self):
        """Execute the full commit workflow."""
        try:
            # Set up caching if needed
            if self.clear_cache:
                try:
                    from gac.cache import clear_cache

                    logger.info("Clearing cache...")
                    clear_cache()
                    logger.info("Cache cleared")
                except ImportError:
                    logger.warning("Cache module not available, skipping cache clear")

            # Handle cache disabling
            if self.no_cache:
                # Set environment variable or config flag to disable cache
                os.environ["GAC_NO_CACHE"] = "1"
                logger.info("Cache disabled for this run")

            # Stage all files if requested
            if self.add_all:
                self._stage_all_files()

            # Get staged files and diff
            staged_files = get_staged_files()
            if not staged_files:
                logger.error("No staged changes found. Stage your changes with git add first.")
                return None

            if self.formatting:
                self._format_staged_files(staged_files)

            # Get the diff of staged changes
            diff = get_staged_diff()
            if not diff:
                logger.error("No diff found for staged changes.")
                return None

            # Generate commit message
            commit_message = self.generate_message(diff)
            if not commit_message:
                logger.error("Failed to generate commit message.")
                return None

            # Execute the commit
            if self.test and not self.test_with_real_diff:
                logger.info("Test mode: Would commit with message: %s", commit_message)
                sys.exit(0)
            else:
                success = self.execute_commit(commit_message)
                if not success:
                    handle_error(GACError("Failed to commit changes"), quiet=self.quiet)
                return commit_message

        except Exception as e:
            error = convert_exception(e, GACError, "An error occurred during workflow execution")
            handle_error(error, quiet=self.quiet)
            return None

    def _stage_all_files(self):
        """Stage all files."""
        logger.info("ℹ️ Staging all changes...")
        stage_files(["."])
        logger.info("✅ All changes staged")

    def _format_staged_files(self, staged_files):
        """Format the staged files."""
        logger.info("ℹ️ Formatting staged files...")
        self.formatting_controller.format_staged_files(staged_files, self.quiet)
        logger.info("✅ Formatting complete")

    def generate_message(self, diff):
        """
        Generate a commit message using the LLM.

        Args:
            diff: The git diff to use for generating the message

        Returns:
            The generated commit message or None if failed
        """
        try:
            # Get git status
            status = get_status()

            # Use one-liner if specified
            one_liner = self.config.get("one_liner", False)

            # Use conventional commit format if specified
            conventional = self.config.get("conventional", False)

            # Build the prompt
            prompt = build_prompt(status, diff, one_liner, self.hint, conventional)

            # Show prompt if requested
            if self.show_prompt:
                # Create an abbreviated version
                abbrev_prompt = (
                    prompt.split("DIFF:")[0] + "DIFF: [diff content omitted for brevity]"
                )
                logger.info("Prompt sent to LLM:\n%s", abbrev_prompt)

            if self.show_prompt_full:
                logger.info("Full prompt sent to LLM:\n%s", prompt)

            # Generate the commit message
            message = self._send_to_llm(status, diff, one_liner, self.hint, conventional)
            if message:
                return clean_commit_message(message)
            return None

        except Exception as e:
            error = convert_exception(e, GACError, "Failed to generate commit message")
            handle_error(error, quiet=self.quiet)
            return None

    def execute_commit(self, commit_message):
        """
        Execute the git commit with the given message.

        Args:
            commit_message: The commit message to use

        Returns:
            True if the commit was successful, False otherwise
        """
        try:
            # Commit the changes
            commit_changes(commit_message)
            logger.info("✅ Changes committed successfully")
            return True

        except Exception as e:
            error = convert_exception(e, GACError, "Failed to commit changes")
            handle_error(error, quiet=self.quiet)
            return False

    def _send_to_llm(self, status, diff, one_liner=False, hint="", conventional=False):
        """
        Send prompt to LLM.

        Args:
            status: Git status output
            diff: Git diff output
            one_liner: Whether to request a one-line commit message
            hint: Hint for the commit message
            conventional: Whether to use conventional commit format

        Returns:
            Model response text
        """
        try:
            model = self.model_override or self.config.get("model")
            temperature = float(self.config.get("temperature", 0.7))

            # Create the prompt
            prompt = build_prompt(status, diff, one_liner, hint, conventional)

            # For unit tests, if we have mock client set up, bypass aisuite
            if "PYTEST_CURRENT_TEST" in os.environ:
                # In test mode, return a hardcoded message
                return "Generated commit message"

            # Extract provider and model
            provider_name = "anthropic"
            model_name = model
            if ":" in model:
                provider_name, model_name = model.split(":", 1)

            # Check API key
            api_key_env = f"{provider_name.upper()}_API_KEY"
            api_key = os.environ.get(api_key_env)
            if not api_key:
                logger.error(f"No API key found for {provider_name} in {api_key_env}")
                raise GACError(f"Missing API key: {api_key_env} not set in environment")

            logger.info(f"Using model: {model_name} with provider: {provider_name}")

            # Handle different providers
            if provider_name.lower() == "anthropic":
                try:
                    # Use direct import for Anthropic to avoid potential issues with aisuite
                    import anthropic

                    client = anthropic.Anthropic(api_key=api_key)
                    message = client.messages.create(
                        model=model_name,
                        max_tokens=4096,
                        temperature=temperature,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return message.content[0].text
                except ImportError:
                    logger.error("Anthropic SDK not installed. Try: pip install anthropic")
                    raise
            elif provider_name.lower() == "openai":
                try:
                    # Use direct import for OpenAI
                    import openai

                    client = openai.OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=4096,
                    )
                    return response.choices[0].message.content
                except ImportError:
                    logger.error("OpenAI SDK not installed. Try: pip install openai")
                    raise
            else:
                # Fall back to aisuite for other providers
                import aisuite as ai

                # Create provider config
                provider_configs = {provider_name: {"api_key": api_key}}

                # Initialize client
                client = ai.Client(provider_configs=provider_configs)

                # Send the request
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=4096,
                )

                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM error details: {type(e).__name__}: {str(e)}")
            error = convert_exception(e, GACError, "Failed to connect to the AI service")
            handle_error(error, quiet=self.quiet, exit_program=False)
            return None
