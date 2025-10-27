"""Tests for Minimax provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gac.errors import AIError
from gac.providers.minimax import call_minimax_api
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest


class TestMinimaxImports:
    """Test that Minimax provider can be imported."""

    def test_import_provider(self):
        """Test that Minimax provider module can be imported."""
        from gac.providers import minimax  # noqa: F401

    def test_import_api_function(self):
        """Test that Minimax API function can be imported."""
        from gac.providers.minimax import call_minimax_api  # noqa: F401


class TestMinimaxAPIKeyValidation:
    """Test Minimax API key validation."""

    def test_missing_api_key_error(self):
        """Test that Minimax raises error when API key is missing."""
        with temporarily_remove_env_var("MINIMAX_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_minimax_api("MiniMax-M2", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "minimax", "MINIMAX_API_KEY")


class TestMinimaxProviderMocked(BaseProviderTest):
    """Mocked tests for Minimax provider."""

    @property
    def provider_name(self) -> str:
        return "minimax"

    @property
    def provider_module(self) -> str:
        return "gac.providers.minimax"

    @property
    def api_function(self) -> Callable:
        return call_minimax_api

    @property
    def api_key_env_var(self) -> str | None:
        return "MINIMAX_API_KEY"

    @property
    def model_name(self) -> str:
        return "MiniMax-M2"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestMinimaxEdgeCases:
    """Test edge cases for Minimax provider."""

    def test_minimax_null_content(self):
        """Test handling of null content."""
        with patch.dict("os.environ", {"MINIMAX_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_minimax_api("MiniMax-M2", [], 0.7, 1000)

                assert "null content" in str(exc_info.value).lower()


@pytest.mark.integration
class TestMinimaxIntegration:
    """Integration tests for Minimax provider."""

    def test_real_api_call(self):
        """Test actual Minimax API call with valid credentials."""
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            pytest.skip("MINIMAX_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_minimax_api(
            model="MiniMax-M2",
            messages=messages,
            temperature=1.0,
            max_tokens=512,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
