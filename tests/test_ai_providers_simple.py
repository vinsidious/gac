import os
import sys
from unittest.mock import MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Mock external dependencies
sys.modules["tiktoken"] = MagicMock()
sys.modules["halo"] = MagicMock()
sys.modules["httpx"] = MagicMock()
sys.modules["gac.constants"] = MagicMock()
sys.modules["gac.errors"] = MagicMock()

from gac import ai_providers  # noqa: E402


def test_ai_providers_functions_exist():
    """Test that all expected functions exist in ai_providers module."""
    assert hasattr(ai_providers, "openai_generate")
    assert hasattr(ai_providers, "anthropic_generate")
    assert hasattr(ai_providers, "groq_generate")
    assert hasattr(ai_providers, "cerebras_generate")
    assert hasattr(ai_providers, "ollama_generate")
    assert hasattr(ai_providers, "count_tokens")
    assert hasattr(ai_providers, "_classify_error")
    assert hasattr(ai_providers, "_extract_text_content")
    assert hasattr(ai_providers, "_get_encoding")


def test_ai_error_class_exists():
    """Test that AIError class exists in ai_providers module."""
    assert hasattr(ai_providers, "AIError")
