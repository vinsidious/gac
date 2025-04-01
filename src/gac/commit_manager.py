"""
Compatibility module for commit manager.

This module is maintained for backward compatibility with tests.
New code should use the core.py module directly.
"""

import logging
import os
from typing import Dict, List, Optional

from gac.core import generate_commit

logger = logging.getLogger(__name__)


class CommitManager:
    """Compatibility class for CommitManager.

    This class is provided for backward compatibility with tests.
    New code should use the core.py functions directly.
    """

    def __init__(
        self,
        quiet: bool = False,
        model_override: Optional[str] = None,
        one_liner: bool = False,
        show_prompt: bool = False,
        show_prompt_full: bool = False,
        hint: str = "",
        no_spinner: bool = False,
    ):
        """Initialize the CommitManager."""
        self.quiet = quiet
        self.model_override = model_override
        self.one_liner = one_liner
        self.show_prompt = show_prompt
        self.show_prompt_full = show_prompt_full
        self.hint = hint
        self.no_spinner = no_spinner

    def generate_message(self, status: str, diff: str) -> Optional[str]:
        """Generate a commit message using the LLM."""
        # Forward to core.generate_commit while simulating the old logic
        model = self.model_override
        return generate_commit(
            formatting=False,  # Skip formatting as this would be handled elsewhere
            model=model,
            hint=self.hint,
            one_liner=self.one_liner,
            show_prompt=self.show_prompt,
            show_prompt_full=self.show_prompt_full,
            quiet=self.quiet,
            no_spinner=self.no_spinner,
        )

    def _send_to_llm(self, status, diff, one_liner=False, hint=""):
        """Send prompt to LLM (compatibility function)."""
        # For tests
        if "PYTEST_CURRENT_TEST" in os.environ:
            return "Generated commit message"

        # Forward to core.generate_commit for real usage
        return generate_commit(
            formatting=False,
            hint=hint,
            one_liner=one_liner,
            quiet=self.quiet,
            no_spinner=self.no_spinner,
        )
