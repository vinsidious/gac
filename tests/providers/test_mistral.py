"""Tests for Mistral AI provider using BaseProviderTest framework."""

import pytest

from tests.providers.conftest import BaseProviderTest


class TestMistralProviderMocked(BaseProviderTest):
    """Mocked HTTP tests for Mistral AI provider inheriting standard test suite."""

    @property
    def provider_name(self) -> str:
        return "mistral"

    # Inherits 9 standard tests from BaseProviderTest:
    # - test_successful_api_call
    # - test_empty_content_handling
    # - test_http_401_authentication_error
    # - test_http_429_rate_limit_error
    # - test_http_500_server_error
    # - test_http_503_service_unavailable
    # - test_connection_error
    # - test_timeout_error
    # - test_malformed_json_response


class TestMistralProviderUnit:
    """Unit tests for Mistral provider - no external dependencies."""

    def test_import_provider(self):
        """Test that Mistral provider can be imported."""
        from gac.providers.mistral import call_mistral_api

        assert callable(call_mistral_api)

    def test_import_api_function(self):
        """Test that Mistral API function is importable from providers package."""
        from gac.providers import call_mistral_api

        assert callable(call_mistral_api)


class TestMistralProviderIntegration:
    """Integration tests with real Mistral API."""

    @pytest.mark.integration
    def test_real_api_call(self):
        """Test actual Mistral API call with valid credentials."""
        import os

        from gac.providers.mistral import call_mistral_api

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            pytest.skip("MISTRAL_API_KEY not set")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, Mistral!'"},
        ]

        try:
            response = call_mistral_api(
                model="mistral-tiny",  # Use their smallest model for testing
                messages=messages,
                temperature=0.7,
                max_tokens=10,
            )
            assert isinstance(response, str)
            assert len(response) > 0
            # Should contain some form of greeting
            assert any(word.lower() in response.lower() for word in ["hello", "mistral", "hi"])
        except Exception as e:
            pytest.fail(f"Real Mistral API call failed: {str(e)}")
