"""Mocked tests for AI provider HTTP interactions.

These tests use mocked HTTP calls to test provider behavior without making real API calls.
"""

import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from gac.errors import AIError
from gac.providers.anthropic import call_anthropic_api
from gac.providers.cerebras import call_cerebras_api
from gac.providers.gemini import call_gemini_api
from gac.providers.groq import call_groq_api
from gac.providers.lmstudio import call_lmstudio_api
from gac.providers.ollama import call_ollama_api
from gac.providers.openai import call_openai_api
from gac.providers.openrouter import call_openrouter_api
from gac.providers.streamlake import call_streamlake_api
from gac.providers.zai import call_zai_api, call_zai_coding_api


class BaseProviderTest(ABC):
    """Base test class defining standard test scenarios all providers should implement.

    Subclasses must define:
    - provider_name: Name of the provider (e.g., "openai")
    - provider_module: Module path (e.g., "gac.providers.openai")
    - api_function: The provider's API call function
    - api_key_env_var: Environment variable for API key (optional, None if not required)
    - model_name: Default model to use in tests
    - success_response: Mock response for successful API call
    - empty_content_response: Mock response with empty content
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'openai')."""
        pass

    @property
    @abstractmethod
    def provider_module(self) -> str:
        """Module path for patching (e.g., 'gac.providers.openai')."""
        pass

    @property
    @abstractmethod
    def api_function(self) -> Callable:
        """The provider's API call function."""
        pass

    @property
    @abstractmethod
    def api_key_env_var(self) -> str | None:
        """Environment variable for API key, or None if not required."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Default model name for tests."""
        pass

    @property
    @abstractmethod
    def success_response(self) -> dict[str, Any]:
        """Mock response for successful API call."""
        pass

    @property
    @abstractmethod
    def empty_content_response(self) -> dict[str, Any]:
        """Mock response with empty content."""
        pass

    def _create_mock_response(self, response_data: dict[str, Any]) -> MagicMock:
        """Create a mock HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status.return_value = None
        return mock_response

    def test_successful_api_call(self):
        """Test that the provider successfully processes a valid API response."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_post.return_value = self._create_mock_response(self.success_response)

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                with patch.dict(os.environ, {self.api_key_env_var: "test-key"}):
                    result = self.api_function(
                        model=self.model_name, messages=messages, temperature=0.7, max_tokens=100
                    )
            else:
                result = self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

            assert result == "feat: Add new feature"
            mock_post.assert_called_once()

    def test_empty_content_handling(self):
        """Test that the provider raises an error for empty content."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_post.return_value = self._create_mock_response(self.empty_content_response)

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(Exception) as exc_info:
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

                error_msg = str(exc_info.value).lower()
                assert "empty content" in error_msg or "missing" in error_msg

    def test_http_401_authentication_error(self):
        """Test that the provider handles HTTP 401 authentication errors."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "invalid-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_http_429_rate_limit_error(self):
        """Test that the provider handles HTTP 429 rate limit errors."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_post.side_effect = httpx.HTTPStatusError(
                "429 Rate limit exceeded", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_http_500_server_error(self):
        """Test that the provider handles HTTP 500 server errors."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_post.side_effect = httpx.HTTPStatusError(
                "500 Internal server error", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_http_503_service_unavailable(self):
        """Test that the provider handles HTTP 503 service unavailable errors."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_post.side_effect = httpx.HTTPStatusError(
                "503 Service unavailable", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_connection_error(self):
        """Test that the provider handles connection errors."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_timeout_error(self):
        """Test that the provider handles timeout errors."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_malformed_json_response(self):
        """Test that the provider handles malformed JSON responses."""
        with patch(f"{self.provider_module}.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            messages = [{"role": "user", "content": "Generate a commit message"}]

            if self.api_key_env_var:
                env_patch = patch.dict(os.environ, {self.api_key_env_var: "test-key"})
            else:
                env_patch = patch.dict(os.environ, {})

            with env_patch:
                with pytest.raises((AIError, ValueError, KeyError, TypeError)):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)


class TestOpenAIProvider(BaseProviderTest):
    """Standard tests for OpenAI provider."""

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


class TestAnthropicProvider(BaseProviderTest):
    """Standard tests for Anthropic provider."""

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


class TestGroqProvider(BaseProviderTest):
    """Standard tests for Groq provider."""

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def provider_module(self) -> str:
        return "gac.providers.groq"

    @property
    def api_function(self) -> Callable:
        return call_groq_api

    @property
    def api_key_env_var(self) -> str | None:
        return "GROQ_API_KEY"

    @property
    def model_name(self) -> str:
        return "llama-3.1-70b"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestCerebrasProvider(BaseProviderTest):
    """Standard tests for Cerebras provider."""

    @property
    def provider_name(self) -> str:
        return "cerebras"

    @property
    def provider_module(self) -> str:
        return "gac.providers.cerebras"

    @property
    def api_function(self) -> Callable:
        return call_cerebras_api

    @property
    def api_key_env_var(self) -> str | None:
        return "CEREBRAS_API_KEY"

    @property
    def model_name(self) -> str:
        return "llama3.1-8b"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestOllamaProvider(BaseProviderTest):
    """Standard tests for Ollama provider."""

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
        return "OLLAMA_API_KEY"  # Optional for remote Ollama

    @property
    def model_name(self) -> str:
        return "llama2"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"response": "feat: Add new feature"}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"response": ""}


class TestOpenRouterProvider(BaseProviderTest):
    """Standard tests for OpenRouter provider."""

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def provider_module(self) -> str:
        return "gac.providers.openrouter"

    @property
    def api_function(self) -> Callable:
        return call_openrouter_api

    @property
    def api_key_env_var(self) -> str | None:
        return "OPENROUTER_API_KEY"

    @property
    def model_name(self) -> str:
        return "mistralai/mistral-7b-instruct"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestStreamLakeProvider(BaseProviderTest):
    """Standard tests for StreamLake provider."""

    @property
    def provider_name(self) -> str:
        return "streamlake"

    @property
    def provider_module(self) -> str:
        return "gac.providers.streamlake"

    @property
    def api_function(self) -> Callable:
        return call_streamlake_api

    @property
    def api_key_env_var(self) -> str | None:
        return "STREAMLAKE_API_KEY"

    @property
    def model_name(self) -> str:
        return "streamlake-test-model"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}

    def test_supports_streamlake_api_key_alias(self):
        """Ensure VC_API_KEY alias works when STREAMLAKE_API_KEY is absent."""
        with patch("gac.providers.streamlake.httpx.post") as mock_post:
            mock_post.return_value = self._create_mock_response(self.success_response)
            messages = [{"role": "user", "content": "Generate a commit message"}]
            with patch.dict(os.environ, {"VC_API_KEY": "alias-key"}, clear=True):
                result = self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)
        assert result == "feat: Add new feature"
        headers = mock_post.call_args.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer alias-key"


class TestGeminiProvider(BaseProviderTest):
    """Standard tests for Gemini provider."""

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


class TestLMStudioProvider(BaseProviderTest):
    """Standard tests for LM Studio provider."""

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
        return "LMSTUDIO_API_KEY"  # Optional for remote LM Studio

    @property
    def model_name(self) -> str:
        return "local-model"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestZAIProvider(BaseProviderTest):
    """Standard tests for ZAI provider."""

    @property
    def provider_name(self) -> str:
        return "zai"

    @property
    def provider_module(self) -> str:
        return "gac.providers.zai"

    @property
    def api_function(self) -> Callable:
        return call_zai_api

    @property
    def api_key_env_var(self) -> str | None:
        return "ZAI_API_KEY"

    @property
    def model_name(self) -> str:
        return "glm-4.5-air"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestZAICodingProvider(BaseProviderTest):
    """Standard tests for ZAI-coding provider."""

    @property
    def provider_name(self) -> str:
        return "zai-coding"

    @property
    def provider_module(self) -> str:
        return "gac.providers.zai"

    @property
    def api_function(self) -> Callable:
        return call_zai_coding_api

    @property
    def api_key_env_var(self) -> str | None:
        return "ZAI_API_KEY"

    @property
    def model_name(self) -> str:
        return "glm-4.5-air"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}
