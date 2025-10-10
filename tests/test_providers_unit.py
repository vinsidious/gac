"""Unit tests for AI provider functionality.

These tests run without any external dependencies and test core logic.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402

from gac.errors import AIError  # noqa: E402


class TestProviderImports:
    """Test that all provider modules can be imported."""

    def test_import_providers(self):
        """Test that all provider modules can be imported."""
        from gac.providers import (  # noqa: F401
            anthropic,
            cerebras,
            gemini,
            groq,
            lmstudio,
            ollama,
            openai,
            openrouter,
            zai,
        )

    def test_import_provider_functions(self):
        """Test that all provider functions can be imported."""
        from gac.providers.anthropic import call_anthropic_api  # noqa: F401
        from gac.providers.cerebras import call_cerebras_api  # noqa: F401
        from gac.providers.gemini import call_gemini_api  # noqa: F401
        from gac.providers.groq import call_groq_api  # noqa: F401
        from gac.providers.lmstudio import call_lmstudio_api  # noqa: F401
        from gac.providers.ollama import call_ollama_api  # noqa: F401
        from gac.providers.openai import call_openai_api  # noqa: F401
        from gac.providers.openrouter import call_openrouter_api  # noqa: F401
        from gac.providers.zai import call_zai_api  # noqa: F401


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""

    def test_openai_api_missing_key(self):
        """Test that OpenAI provider raises error when API key is missing."""
        original_key = os.getenv("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]

        try:
            from gac.providers.openai import call_openai_api

            with pytest.raises(AIError) as exc_info:
                call_openai_api("gpt-4", [], 0.7, 1000)

            assert "OPENAI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""

    def test_anthropic_api_missing_key(self):
        """Test that Anthropic provider raises error when API key is missing."""
        original_key = os.getenv("ANTHROPIC_API_KEY")
        if original_key:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            from gac.providers.anthropic import call_anthropic_api

            with pytest.raises(AIError) as exc_info:
                call_anthropic_api("claude-3", [], 0.7, 1000)

            assert "ANTHROPIC_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key


class TestGroqProvider:
    """Test Groq provider functionality."""

    def test_groq_api_missing_key(self):
        """Test that Groq provider raises error when API key is missing."""
        original_key = os.getenv("GROQ_API_KEY")
        if original_key:
            del os.environ["GROQ_API_KEY"]

        try:
            from gac.providers.groq import call_groq_api

            with pytest.raises(AIError) as exc_info:
                call_groq_api("llama-3.1-70b", [], 0.7, 1000)

            assert "GROQ_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["GROQ_API_KEY"] = original_key


class TestCerebrasProvider:
    """Test Cerebras provider functionality."""

    def test_cerebras_api_missing_key(self):
        """Test that Cerebras provider raises error when API key is missing."""
        original_key = os.getenv("CEREBRAS_API_KEY")
        if original_key:
            del os.environ["CEREBRAS_API_KEY"]

        try:
            from gac.providers.cerebras import call_cerebras_api

            with pytest.raises(AIError) as exc_info:
                call_cerebras_api("llama3.1-8b", [], 0.7, 1000)

            assert "CEREBRAS_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["CEREBRAS_API_KEY"] = original_key


class TestOllamaProvider:
    """Test Ollama provider functionality."""

    def test_ollama_api_import(self):
        """Test that call_ollama_api can be imported."""
        from gac.providers.ollama import call_ollama_api

        assert callable(call_ollama_api)


class TestOpenRouterProvider:
    """Test OpenRouter provider functionality."""

    def test_openrouter_api_missing_key(self):
        """Test that OpenRouter provider raises error when API key is missing."""
        original_key = os.getenv("OPENROUTER_API_KEY")
        if original_key:
            del os.environ["OPENROUTER_API_KEY"]

        try:
            from gac.providers.openrouter import call_openrouter_api

            with pytest.raises(AIError) as exc_info:
                call_openrouter_api("mistralai/mistral-7b-instruct", [], 0.7, 1000)

            assert "OPENROUTER_API_KEY environment variable not set" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key


class TestGeminiProvider:
    """Test Gemini provider functionality."""

    def test_gemini_api_missing_key(self):
        """Test that Gemini provider raises error when API key is missing."""
        original_key = os.getenv("GEMINI_API_KEY")
        if original_key:
            del os.environ["GEMINI_API_KEY"]

        try:
            from gac.providers.gemini import call_gemini_api

            with pytest.raises(AIError) as exc_info:
                call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

            assert "GEMINI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["GEMINI_API_KEY"] = original_key


class TestLMStudioProvider:
    """Test LM Studio provider functionality."""

    def test_lmstudio_api_import(self):
        """Test that call_lmstudio_api can be imported."""
        from gac.providers.lmstudio import call_lmstudio_api

        assert callable(call_lmstudio_api)


class TestZAIProvider:
    """Test ZAI provider functionality."""

    def test_zai_api_import(self):
        """Test that call_zai_api can be imported."""
        from gac.providers.zai import call_zai_api

        assert callable(call_zai_api)

    def test_zai_api_missing_key(self):
        """Test that ZAI provider raises error when API key is missing."""
        original_key = os.getenv("ZAI_API_KEY")
        if original_key:
            del os.environ["ZAI_API_KEY"]

        try:
            from gac.providers.zai import call_zai_api

            with pytest.raises(AIError) as exc_info:
                call_zai_api("model", [], 0.7, 1000)

            assert "ZAI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["ZAI_API_KEY"] = original_key

    def test_zai_coding_api_import(self):
        """Test that call_zai_coding_api can be imported."""
        from gac.providers.zai import call_zai_coding_api

        assert callable(call_zai_coding_api)

    def test_zai_coding_api_missing_key(self):
        """Test that ZAI-coding provider raises error when API key is missing."""
        original_key = os.getenv("ZAI_API_KEY")
        if original_key:
            del os.environ["ZAI_API_KEY"]

        try:
            from gac.providers.zai import call_zai_coding_api

            with pytest.raises(AIError) as exc_info:
                call_zai_coding_api("model", [], 0.7, 1000)

            assert "ZAI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["ZAI_API_KEY"] = original_key
