"""Tests for Gemini provider."""

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

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


class TestGeminiEdgeCases:
    """Test edge cases for Gemini provider."""

    def test_gemini_missing_candidates(self):
        """Test handling of response without candidates field."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"some_other_field": "value"}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

                assert "missing candidates" in str(exc_info.value).lower()

    def test_gemini_empty_candidates(self):
        """Test handling of empty candidates array."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": []}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

                assert "missing candidates" in str(exc_info.value).lower()

    def test_gemini_missing_content(self):
        """Test handling of candidate without content field."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"no_content": "here"}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

                assert "invalid content structure" in str(exc_info.value).lower()

    def test_gemini_missing_parts(self):
        """Test handling of content without parts field."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"content": {"no_parts": []}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

                assert "invalid content structure" in str(exc_info.value).lower()

    def test_gemini_empty_parts(self):
        """Test handling of empty parts array."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"content": {"parts": []}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

                assert "invalid content structure" in str(exc_info.value).lower()

    def test_gemini_null_text_content(self):
        """Test handling of null text in parts."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": None}]}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_gemini_api("gemini-1.5-pro", [], 0.7, 1000)

                assert "missing text content" in str(exc_info.value).lower()

    def test_gemini_system_message_handling(self):
        """Test system message conversion to Gemini format."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "test response"}]}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                messages = [
                    {"role": "system", "content": "System instruction"},
                    {"role": "user", "content": "User message"},
                ]

                result = call_gemini_api("gemini-1.5-pro", messages, 0.7, 1000)

                # Verify the payload structure
                call_args = mock_post.call_args
                payload = call_args.kwargs["json"]
                assert len(payload["contents"]) == 1
                assert payload["contents"][0]["role"] == "user"
                assert payload["systemInstruction"]["role"] == "system"
                assert payload["systemInstruction"]["parts"][0]["text"] == "System instruction"
                assert result == "test response"

    def test_gemini_blank_system_message_ignored(self):
        """Ensure blank system instructions are omitted from payload."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                messages = [
                    {"role": "system", "content": "   "},
                    {"role": "user", "content": "User message"},
                ]

                call_gemini_api("gemini-1.5-pro", messages, 0.7, 1000)

                payload = mock_post.call_args.kwargs["json"]
                assert "systemInstruction" not in payload
                assert len(payload["contents"]) == 1
                assert payload["contents"][0]["role"] == "user"

    def test_gemini_assistant_message_conversion(self):
        """Test assistant message converted to model role."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "test response"}]}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                messages = [
                    {"role": "user", "content": "First message"},
                    {"role": "assistant", "content": "Assistant reply"},
                    {"role": "user", "content": "Second message"},
                ]

                result = call_gemini_api("gemini-1.5-pro", messages, 0.7, 1000)

                # Verify the payload structure
                call_args = mock_post.call_args
                payload = call_args.kwargs["json"]
                assert len(payload["contents"]) == 3
                assert payload["contents"][0]["role"] == "user"
                assert payload["contents"][1]["role"] == "model"  # assistant -> model
                assert payload["contents"][2]["role"] == "user"
                assert result == "test response"

    def test_gemini_ignores_empty_text_parts(self):
        """Ensure empty parts are skipped when extracting model text."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": ""},
                                    {"text": "final answer"},
                                ]
                            }
                        }
                    ]
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                result = call_gemini_api(
                    "gemini-1.5-pro",
                    [{"role": "user", "content": "hi"}],
                    temperature=0.7,
                    max_tokens=1000,
                )

                assert result == "final answer"
