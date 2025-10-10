"""Unit tests for AI provider functionality.

These tests run without any external dependencies and test core logic.
"""

import pytest

from gac.errors import AIError
from tests.provider_test_utils import (
    assert_import_success,
    assert_missing_api_key_error,
    get_api_key_providers,
    get_local_providers,
    temporarily_remove_env_var,
)


class TestProviderImports:
    """Test that all provider modules can be imported."""

    def test_import_providers(self):
        """Test that all provider modules can be imported."""
        from gac.providers import (  # noqa: F401
            anthropic,
            cerebras,
            gemini,
            groq,
            lmstudio,
            ollama,
            openai,
            openrouter,
            streamlake,
            zai,
        )

    def test_import_provider_functions(self):
        """Test that all provider functions can be imported."""
        from gac.providers.anthropic import call_anthropic_api  # noqa: F401
        from gac.providers.cerebras import call_cerebras_api  # noqa: F401
        from gac.providers.gemini import call_gemini_api  # noqa: F401
        from gac.providers.groq import call_groq_api  # noqa: F401
        from gac.providers.lmstudio import call_lmstudio_api  # noqa: F401
        from gac.providers.ollama import call_ollama_api  # noqa: F401
        from gac.providers.openai import call_openai_api  # noqa: F401
        from gac.providers.openrouter import call_openrouter_api  # noqa: F401
        from gac.providers.streamlake import call_streamlake_api  # noqa: F401
        from gac.providers.zai import call_zai_api, call_zai_coding_api  # noqa: F401


class TestProviderAPIKeyValidation:
    """Parameterized tests for API key validation across all providers."""

    @pytest.mark.parametrize("test_case", get_api_key_providers(), ids=lambda tc: tc.name)
    def test_missing_api_key_error(self, test_case):
        """Test that providers raise appropriate errors when API key is missing."""
        with temporarily_remove_env_var(test_case.env_var):
            with pytest.raises(AIError) as exc_info:
                test_case.api_function(test_case.test_model, [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, test_case.name, test_case.env_var)

    def test_zai_coding_function_missing_api_key(self):
        """Test that ZAI's coding function raises error when API key is missing."""
        from gac.providers.zai import call_zai_coding_api

        with temporarily_remove_env_var("ZAI_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_zai_coding_api("glm-4.5-air", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "zai", "ZAI_API_KEY")


class TestLocalProviderImports:
    """Tests for local providers that don't require API keys."""

    @pytest.mark.parametrize("test_case", get_local_providers(), ids=lambda tc: tc.name)
    def test_local_provider_import(self, test_case):
        """Test that local provider functions can be imported and are callable."""
        assert_import_success(test_case.import_function)
