import os
import sys

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.errors import AIError  # noqa: E402
from gac.providers.anthropic import call_anthropic_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api


class TestAIProvidersIntegration:
    """Integration tests for ai_providers module."""

    def test_openai_generate_missing_api_key(self):
        """Test that call_openai_api raises AIError when API key is missing."""
        # Temporarily remove the API key if it exists
        original_key = os.getenv("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_openai_api(model="gpt-4", messages=messages, temperature=0.7, max_tokens=100)
            assert "OPENAI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            # Restore the API key if it existed
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_anthropic_generate_missing_api_key(self):
        """Test that call_anthropic_api raises AIError when API key is missing."""
        # Temporarily remove the API key if it exists
        original_key = os.getenv("ANTHROPIC_API_KEY")
        if original_key:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_anthropic_api(model="claude-3-haiku", messages=messages, temperature=0.7, max_tokens=100)
            assert "ANTHROPIC_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            # Restore the API key if it existed
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

    def test_openrouter_generate_missing_api_key(self):
        """Test that call_openrouter_api raises AIError when API key is missing."""
        original_key = os.getenv("OPENROUTER_API_KEY")
        if original_key:
            del os.environ["OPENROUTER_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_openrouter_api(model="openrouter/auto", messages=messages, temperature=0.7, max_tokens=100)
            assert "OPENROUTER_API_KEY environment variable not set" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key
