"""Tests for Gemini provider."""

from collections.abc import Callable
from typing import Any

import pytest

from gac.errors import AIError
from gac.providers.gemini import call_gemini_api
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest


class TestGeminiImports:
    """Test that Gemini provider can be imported."""

    def test_import_provider(self):
        """Test that Gemini provider module can be imported."""
        from gac.providers import gemini  # noqa: F401

    def test_import_api_function(self):
        """Test that Gemini API function can be imported."""
        from gac.providers.gemini import call_gemini_api  # noqa: F401


class TestGeminiAPIKeyValidation:
    """Test Gemini API key validation."""

    def test_missing_api_key_error(self):
        """Test that Gemini raises error when API key is missing."""
        with temporarily_remove_env_var("GEMINI_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "gemini", "GEMINI_API_KEY")


class TestGeminiProviderMocked(BaseProviderTest):
    """Mocked tests for Gemini provider."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def provider_module(self) -> str:
        return "gac.providers.gemini"

    @property
    def api_function(self) -> Callable:
        return call_gemini_api

    @property
    def api_key_env_var(self) -> str | None:
        return "GEMINI_API_KEY"

    @property
    def model_name(self) -> str:
        return "gemini-1.5-pro"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"candidates": [{"content": {"parts": [{"text": "feat: Add new feature"}]}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"candidates": [{"content": {"parts": [{"text": ""}]}}]}
