"""Tests for Ollama provider."""

import os
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from gac.errors import AIError
from gac.providers.ollama import call_ollama_api
from tests.provider_test_utils import assert_import_success
from tests.providers.conftest import BaseProviderTest


class TestOllamaImports:
    """Test that Ollama provider can be imported."""

    def test_import_provider(self):
        """Test that Ollama provider module can be imported."""
        from gac.providers import ollama  # noqa: F401

    def test_import_api_function(self):
        """Test that Ollama API function can be imported and is callable."""
        from gac.providers.ollama import call_ollama_api

        assert_import_success(call_ollama_api)


class TestOllamaProviderMocked(BaseProviderTest):
    """Mocked tests for Ollama provider."""

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def provider_module(self) -> str:
        return "gac.providers.ollama"

    @property
    def api_function(self) -> Callable:
        return call_ollama_api

    @property
    def api_key_env_var(self) -> str | None:
        return "OLLAMA_API_KEY"

    @property
    def model_name(self) -> str:
        return "llama2"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"response": "feat: Add new feature"}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"response": ""}


@pytest.mark.providers
class TestOllamaIntegration:
    """Integration tests for Ollama provider."""

    def test_real_api_call(self):
        """Test actual Ollama API call with local instance."""
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
