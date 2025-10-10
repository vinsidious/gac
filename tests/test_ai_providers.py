"""Tests for ai_providers module."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.errors import AIError
from gac.providers.anthropic import call_anthropic_api
from gac.providers.cerebras import call_cerebras_api
from gac.providers.groq import call_groq_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api
from gac.providers.streamlake import call_streamlake_api


class TestAPIKeyValidation:
    """Tests for API key validation in each provider."""

    def test_openai_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_openai_api(
                    model="gpt-4", messages=[{"role": "user", "content": "test"}], temperature=0.7, max_tokens=100
                )
            assert "OPENAI_API_KEY not found in environment variables" in str(exc_info.value)

    def test_anthropic_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_anthropic_api(
                    model="claude-3-haiku",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "ANTHROPIC_API_KEY not found in environment variables" in str(exc_info.value)

    def test_cerebras_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_cerebras_api(
                    model="llama3.1-8b", messages=[{"role": "user", "content": "test"}], temperature=0.7, max_tokens=100
                )
            assert "CEREBRAS_API_KEY not found in environment variables" in str(exc_info.value)

    def test_groq_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        # Temporarily remove the API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_groq_api(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "GROQ_API_KEY not found in environment variables" in str(exc_info.value)

    def test_openrouter_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_openrouter_api(
                    model="openrouter/auto",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "OPENROUTER_API_KEY environment variable not set" in str(exc_info.value)

    def test_streamlake_generate_missing_api_key(self):
        """Test that AIError is raised when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIError) as exc_info:
                call_streamlake_api(
                    model="ep-gmlysa-1760118602179985967",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "STREAMLAKE_API_KEY not found in environment variables" in str(exc_info.value)
