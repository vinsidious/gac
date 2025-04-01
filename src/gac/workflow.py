"""
Compatibility module for workflow.

This module is maintained for backward compatibility with tests.
New code should use the core.py module directly.
"""

import logging
from typing import Optional

from gac.commit_manager import CommitManager
from gac.core import commit_changes
from gac.formatting_controller import FormattingController

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
    return commit_manager._send_to_llm("", prompt, False, "")


class CommitWorkflow:
    """Compatibility class for CommitWorkflow.

    This class is provided for backward compatibility with tests.
    New code should use the core.py functions directly.
    """

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
        no_spinner: bool = False,
        formatter: str = None,
        formatting: bool = True,
        model_override: str = None,
        push: bool = False,
    ):
        """Initialize the CommitWorkflow."""
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
        self.one_liner = one_liner
        self.show_prompt = show_prompt
        self.show_prompt_full = show_prompt_full
        self.no_spinner = no_spinner

        # Initialize components (for backward compatibility)
        self.formatting_controller = FormattingController()
        self.commit_manager = CommitManager(
            quiet=quiet,
            model_override=self.model_override,
            one_liner=one_liner,
            show_prompt=show_prompt,
            show_prompt_full=show_prompt_full,
            hint=hint,
            no_spinner=no_spinner,
        )

    def run(self):
        """Execute the full commit workflow."""
        return commit_changes(
            force=self.force,
            add_all=self.add_all,
            formatting=self.formatting,
            model=self.model_override,
            hint=self.hint,
            one_liner=self.one_liner,
            show_prompt=self.show_prompt,
            show_prompt_full=self.show_prompt_full,
            quiet=self.quiet,
            no_spinner=self.no_spinner,
            push=self.push,
        )
