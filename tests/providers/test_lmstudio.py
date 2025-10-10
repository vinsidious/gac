"""Tests for LM Studio provider."""

from collections.abc import Callable
from typing import Any

import pytest

from gac.errors import AIError
from gac.providers.lmstudio import call_lmstudio_api
from tests.provider_test_utils import assert_import_success, temporarily_set_env_var
from tests.providers.conftest import BaseProviderTest


class TestLMStudioImports:
    """Test that LM Studio provider can be imported."""

    def test_import_provider(self):
        """Test that LM Studio provider module can be imported."""
        from gac.providers import lmstudio  # noqa: F401

    def test_import_api_function(self):
        """Test that LM Studio API function can be imported and is callable."""
        from gac.providers.lmstudio import call_lmstudio_api

        assert_import_success(call_lmstudio_api)


class TestLMStudioProviderMocked(BaseProviderTest):
    """Mocked tests for LM Studio provider."""

    @property
    def provider_name(self) -> str:
        return "lmstudio"

    @property
    def provider_module(self) -> str:
        return "gac.providers.lmstudio"

    @property
    def api_function(self) -> Callable:
        return call_lmstudio_api

    @property
    def api_key_env_var(self) -> str | None:
        return "LMSTUDIO_API_KEY"

    @property
    def model_name(self) -> str:
        return "local-model"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


@pytest.mark.providers
class TestLMStudioIntegration:
    """Integration tests for LM Studio provider."""

    def test_connection_error(self):
        """Test that call_lmstudio_api raises connection error when server is unreachable."""
        with temporarily_set_env_var("LMSTUDIO_API_URL", "http://127.0.0.1:9"):
            with pytest.raises(AIError) as exc_info:
                messages = [{"role": "user", "content": "test prompt"}]
                call_lmstudio_api(model="local-model", messages=messages, temperature=1.0, max_tokens=20)
            assert "LM Studio connection failed" in str(exc_info.value)
