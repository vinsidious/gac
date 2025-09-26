import os
import sys

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.ai_providers import anthropic_generate, openai_generate  # noqa: E402
from gac.errors import AIError  # noqa: E402


class TestAIProvidersIntegration:
    """Integration tests for ai_providers module."""

    def test_openai_generate_missing_api_key(self):
        """Test that openai_generate raises AIError when API key is missing."""
        # Temporarily remove the API key if it exists
        original_key = os.getenv("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                openai_generate(model="gpt-4", prompt="test prompt", quiet=True)
            assert "OPENAI_API_KEY environment variable not set" in str(exc_info.value)
        finally:
            # Restore the API key if it existed
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_anthropic_generate_missing_api_key(self):
        """Test that anthropic_generate raises AIError when API key is missing."""
        # Temporarily remove the API key if it exists
        original_key = os.getenv("ANTHROPIC_API_KEY")
        if original_key:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                anthropic_generate(model="claude-3-haiku", prompt="test prompt", quiet=True)
            assert "ANTHROPIC_API_KEY environment variable not set" in str(exc_info.value)
        finally:
            # Restore the API key if it existed
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key
