"""Tests for Anthropic provider."""

import os
from collections.abc import Callable
from typing import Any

import pytest

from gac.errors import AIError
from gac.providers.anthropic import call_anthropic_api
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest


class TestAnthropicImports:
    """Test that Anthropic provider can be imported."""

    def test_import_provider(self):
        """Test that Anthropic provider module can be imported."""
        from gac.providers import anthropic  # noqa: F401

    def test_import_api_function(self):
        """Test that Anthropic API function can be imported."""
        from gac.providers.anthropic import call_anthropic_api  # noqa: F401


class TestAnthropicAPIKeyValidation:
    """Test Anthropic API key validation."""

    def test_missing_api_key_error(self):
        """Test that Anthropic raises error when API key is missing."""
        with temporarily_remove_env_var("ANTHROPIC_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_anthropic_api("claude-3-haiku-20240307", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "anthropic", "ANTHROPIC_API_KEY")


class TestAnthropicProviderMocked(BaseProviderTest):
    """Mocked tests for Anthropic provider."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def provider_module(self) -> str:
        return "gac.providers.anthropic"

    @property
    def api_function(self) -> Callable:
        return call_anthropic_api

    @property
    def api_key_env_var(self) -> str | None:
        return "ANTHROPIC_API_KEY"

    @property
    def model_name(self) -> str:
        return "claude-3"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"content": [{"text": "feat: Add new feature"}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"content": [{"text": ""}]}


@pytest.mark.providers
class TestAnthropicIntegration:
    """Integration tests for Anthropic provider."""

    def test_real_api_call(self):
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
