"""Tests for OpenAI provider."""

import os
from collections.abc import Callable
from typing import Any

import pytest

from gac.errors import AIError
from gac.providers.openai import call_openai_api
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest


class TestOpenAIImports:
    """Test that OpenAI provider can be imported."""

    def test_import_provider(self):
        """Test that OpenAI provider module can be imported."""
        from gac.providers import openai  # noqa: F401

    def test_import_api_function(self):
        """Test that OpenAI API function can be imported."""
        from gac.providers.openai import call_openai_api  # noqa: F401


class TestOpenAIAPIKeyValidation:
    """Test OpenAI API key validation."""

    def test_missing_api_key_error(self):
        """Test that OpenAI raises error when API key is missing."""
        with temporarily_remove_env_var("OPENAI_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_openai_api("gpt-4", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "openai", "OPENAI_API_KEY")


class TestOpenAIProviderMocked(BaseProviderTest):
    """Mocked tests for OpenAI provider."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def provider_module(self) -> str:
        return "gac.providers.openai"

    @property
    def api_function(self) -> Callable:
        return call_openai_api

    @property
    def api_key_env_var(self) -> str | None:
        return "OPENAI_API_KEY"

    @property
    def model_name(self) -> str:
        return "gpt-4"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI provider."""

    def test_real_api_call(self):
        """Test actual OpenAI API call with valid credentials."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_openai_api(model="gpt-4.1-nano", messages=messages, temperature=1.0, max_tokens=50)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
