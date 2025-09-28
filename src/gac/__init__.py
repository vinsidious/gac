"""Git Auto Commit (gac) - Generate commit messages using AI."""

from gac.__version__ import __version__
from gac.ai import generate_commit_message
from gac.git import get_staged_files, push_changes
from gac.prompt import build_prompt, clean_commit_message
from gac.providers.anthropic import call_anthropic_api as anthropic_generate
from gac.providers.cerebras import call_cerebras_api as cerebras_generate
from gac.providers.groq import call_groq_api as groq_generate
from gac.providers.ollama import call_ollama_api as ollama_generate
from gac.providers.openai import call_openai_api as openai_generate
from gac.providers.openrouter import call_openrouter_api as openrouter_generate

__all__ = [
    "__version__",
    "generate_commit_message",
    "build_prompt",
    "clean_commit_message",
    "get_staged_files",
    "push_changes",
    "anthropic_generate",
    "cerebras_generate",
    "groq_generate",
    "ollama_generate",
    "openai_generate",
    "openrouter_generate",
]
