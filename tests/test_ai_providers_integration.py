"""Integration tests for AI provider API calls.

These tests make real API calls and are marked with @pytest.mark.providers.
By default, they are skipped unless explicitly requested.

Run with:
    make test-providers  # Run only provider tests
    make test-all        # Run all tests including providers
"""

import os
import sys

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.errors import AIError  # noqa: E402
from gac.providers.anthropic import call_anthropic_api
from gac.providers.cerebras import call_cerebras_api
from gac.providers.groq import call_groq_api
from gac.providers.ollama import call_ollama_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api
from gac.providers.zai import call_zai_api


class TestAIProvidersIntegration:
    """Integration tests for ai_providers module."""

    def test_anthropic_generate_missing_api_key(self):
        """Test that call_anthropic_api raises AIError when API key is missing."""
        original_key = os.getenv("ANTHROPIC_API_KEY")
        if original_key:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_anthropic_api(model="claude-3-haiku", messages=messages, temperature=0.7, max_tokens=100)
            assert "ANTHROPIC_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

    def test_cerebras_generate_missing_api_key(self):
        """Test that call_cerebras_api raises AIError when API key is missing."""
        original_key = os.getenv("CEREBRAS_API_KEY")
        if original_key:
            del os.environ["CEREBRAS_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_cerebras_api(model="llama3.1-8b", messages=messages, temperature=0.7, max_tokens=100)
            assert "CEREBRAS_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["CEREBRAS_API_KEY"] = original_key

    def test_groq_generate_missing_api_key(self):
        """Test that call_groq_api raises AIError when API key is missing."""
        original_key = os.getenv("GROQ_API_KEY")
        if original_key:
            del os.environ["GROQ_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_groq_api(model="llama-3.3-70b-versatile", messages=messages, temperature=0.7, max_tokens=100)
            assert "GROQ_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["GROQ_API_KEY"] = original_key

    def test_openai_generate_missing_api_key(self):
        """Test that call_openai_api raises AIError when API key is missing."""
        original_key = os.getenv("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_openai_api(model="gpt-4", messages=messages, temperature=0.7, max_tokens=100)
            assert "OPENAI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

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

    def test_zai_generate_missing_api_key(self):
        """Test that call_zai_api raises AIError when API key is missing."""
        original_key = os.getenv("ZAI_API_KEY")
        if original_key:
            del os.environ["ZAI_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_zai_api(model="glm-4.5-air", messages=messages, temperature=0.7, max_tokens=100)
            assert "ZAI_API_KEY not found in environment variables" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["ZAI_API_KEY"] = original_key


@pytest.mark.providers
class TestRealAPICallsAnthropic:
    """Real API call tests for Anthropic."""

    def test_anthropic_real_api_call(self):
        """Test actual Anthropic API call with valid credentials."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_anthropic_api(
            model="claude-3-haiku-20240307", messages=messages, temperature=0.7, max_tokens=50
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.providers
class TestRealAPICallsCerebras:
    """Real API call tests for Cerebras."""

    def test_cerebras_real_api_call(self):
        """Test actual Cerebras API call with valid credentials."""
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            pytest.skip("CEREBRAS_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_cerebras_api(model="qwen-3-coder-480b", messages=messages, temperature=0.7, max_tokens=50)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.providers
class TestRealAPICallsGroq:
    """Real API call tests for Groq."""

    def test_groq_real_api_call(self):
        """Test actual Groq API call with valid credentials."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            pytest.skip("GROQ_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_groq_api(model="llama-3.3-70b-versatile", messages=messages, temperature=0.7, max_tokens=50)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.providers
class TestRealAPICallsOllama:
    """Real API call tests for Ollama (local)."""

    def test_ollama_real_api_call(self):
        """Test actual Ollama API call with local instance."""
        import httpx

        # Check if Ollama is running before attempting the test
        api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        try:
            response = httpx.get(f"{api_url.rstrip('/')}/api/tags", timeout=2)
            if response.status_code != 200:
                pytest.skip("Ollama is not running - skipping real API test")
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Ollama is not running - skipping real API test")

        try:
            messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
            response = call_ollama_api(model="gpt-oss:20b", messages=messages, temperature=0.7, max_tokens=50)

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        except AIError as e:
            error_str = str(e).lower()
            if "not found" in error_str:
                pytest.skip(f"Ollama model not found - skipping real API test: {e}")
            raise


@pytest.mark.providers
class TestRealAPICallsOpenAI:
    """Real API call tests for OpenAI."""

    def test_openai_real_api_call(self):
        """Test actual OpenAI API call with valid credentials."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_openai_api(model="gpt-4.1-nano", messages=messages, temperature=0.7, max_tokens=50)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.providers
class TestRealAPICallsOpenRouter:
    """Real API call tests for OpenRouter."""

    def test_openrouter_real_api_call(self):
        """Test actual OpenRouter API call with valid credentials."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_openrouter_api(model="openrouter/auto", messages=messages, temperature=0.7, max_tokens=50)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.providers
class TestRealAPICallsZAI:
    """Real API call tests for Z.AI."""

    def test_zai_real_api_call(self):
        """Test actual Z.AI API call with valid credentials."""
        api_key = os.getenv("ZAI_API_KEY")
        if not api_key:
            pytest.skip("ZAI_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        try:
            response = call_zai_api(model="glm-4.5-air", messages=messages, temperature=0.7, max_tokens=50)

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            if "empty content" in str(e) or "null content" in str(e):
                pytest.skip(f"Z.AI API returned empty content - possible configuration issue: {e}")
            else:
                raise
