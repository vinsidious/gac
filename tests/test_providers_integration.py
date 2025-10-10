"""Integration tests for AI provider API calls.

These tests make real API calls and are marked with @pytest.mark.providers.
By default, they are skipped unless explicitly requested.

Run with:
    make test-providers  # Run only provider tests
    make test-all        # Run all tests including providers
"""

import os
import sys
from contextlib import contextmanager

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gac.errors import AIError
from gac.providers.anthropic import call_anthropic_api
from gac.providers.cerebras import call_cerebras_api
from gac.providers.groq import call_groq_api
from gac.providers.lmstudio import call_lmstudio_api
from gac.providers.ollama import call_ollama_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api
from gac.providers.streamlake import call_streamlake_api
from gac.providers.zai import call_zai_api
from tests.provider_test_utils import (
    assert_missing_api_key_error,
    get_api_key_providers,
    temporarily_remove_env_var,
)


@contextmanager
def temporarily_set_env_var(env_var: str, value: str):
    """Temporarily set an environment variable and restore it after the test.

    Args:
        env_var: The environment variable name to set
        value: The value to set
    """
    original_value = os.getenv(env_var)
    os.environ[env_var] = value

    try:
        yield
    finally:
        if original_value is not None:
            os.environ[env_var] = original_value
        else:
            del os.environ[env_var]


@pytest.mark.providers
class TestProviderErrorHandling:
    """Integration tests for provider error handling."""

    @pytest.mark.parametrize("test_case", get_api_key_providers(), ids=lambda tc: tc.name)
    def test_missing_api_key_error(self, test_case):
        """Test that providers raise appropriate errors when API key is missing."""
        messages = [{"role": "user", "content": "test prompt"}]

        with temporarily_remove_env_var(test_case.env_var):
            with pytest.raises(AIError) as exc_info:
                test_case.api_function(model=test_case.test_model, messages=messages, temperature=1.0, max_tokens=100)

            assert_missing_api_key_error(exc_info, test_case.name, test_case.env_var)

    def test_lmstudio_connection_error(self):
        """Test that call_lmstudio_api raises connection error when server is unreachable."""
        with temporarily_set_env_var("LMSTUDIO_API_URL", "http://127.0.0.1:9"):
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_lmstudio_api(model="local-model", messages=messages, temperature=1.0, max_tokens=20)
            assert "LM Studio connection failed" in str(exc_info.value)


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
            model="claude-3-haiku-20240307", messages=messages, temperature=1.0, max_tokens=50
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
        try:
            response = call_cerebras_api(model="qwen-3-coder-480b", messages=messages, temperature=1.0, max_tokens=50)

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        except AIError as e:
            # If we get a rate limit error, skip the test rather than fail
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                pytest.skip(f"Cerebras API rate limit exceeded - skipping real API test: {e}")
            raise


@pytest.mark.providers
class TestRealAPICallsGroq:
    """Real API call tests for Groq."""

    def test_groq_real_api_call(self):
        """Test actual Groq API call with valid credentials."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            pytest.skip("GROQ_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_groq_api(model="llama-3.3-70b-versatile", messages=messages, temperature=1.0, max_tokens=50)

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
            response = call_ollama_api(model="gpt-oss:20b", messages=messages, temperature=1.0, max_tokens=50)

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
        response = call_openai_api(model="gpt-4.1-nano", messages=messages, temperature=1.0, max_tokens=50)

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
        try:
            response = call_openrouter_api(
                model="mistralai/mistral-7b-instruct", messages=messages, temperature=1.0, max_tokens=50
            )

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        except AIError as e:
            # If we get an auth error, rate limit error, or service unavailable error, skip the test rather than fail
            error_str = str(e).lower()
            if "401" in error_str or "unauthorized" in error_str or "auth" in error_str:
                pytest.skip(f"OpenRouter API authentication failed - skipping real API test: {e}")
            elif "429" in error_str or "rate limit" in error_str:
                pytest.skip(f"OpenRouter API rate limit exceeded - skipping real API test: {e}")
            elif (
                "502" in error_str
                or "503" in error_str
                or "service unavailable" in error_str
                or "connection error" in error_str
            ):
                pytest.skip(f"OpenRouter API service unavailable - skipping real API test: {e}")
            raise


@pytest.mark.providers
class TestRealAPICallsStreamLake:
    """Real API call tests for StreamLake (Vanchin)."""

    def test_streamlake_real_api_call(self):
        """Test actual StreamLake API call with valid credentials."""
        api_key = os.getenv("STREAMLAKE_API_KEY") or os.getenv("VC_API_KEY")
        if not api_key:
            pytest.skip("STREAMLAKE_API_KEY not set - skipping real API test (VC_API_KEY alias also missing)")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        try:
            response = call_streamlake_api(
                model="ep-gmlysa-1760118602179985967",
                messages=messages,
                temperature=1.0,
                max_tokens=50,
            )

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        except AIError as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                pytest.skip(f"StreamLake API rate limit exceeded - skipping real API test: {e}")
            elif "401" in error_str or "unauthorized" in error_str or "auth" in error_str:
                pytest.skip(f"StreamLake API authentication failed - skipping real API test: {e}")
            raise


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
            response = call_zai_api(model="glm-4.5-air", messages=messages, temperature=1.0, max_tokens=50)

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            if "empty content" in str(e) or "null content" in str(e):
                pytest.skip(f"Z.AI API returned empty content - possible configuration issue: {e}")
            else:
                raise
