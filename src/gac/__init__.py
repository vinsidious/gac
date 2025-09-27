"""Git Auto Commit (gac) - Generate commit messages using AI."""

from gac.__version__ import __version__
from gac.ai import generate_commit_message
from gac.git import get_staged_files, push_changes
from gac.prompt import build_prompt, clean_commit_message
from gac.providers.anthropic import generate as anthropic_generate
from gac.providers.cerebras import generate as cerebras_generate
from gac.providers.groq import generate as groq_generate
from gac.providers.ollama import generate as ollama_generate
from gac.providers.openai import generate as openai_generate
from gac.providers.openrouter import generate as openrouter_generate

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
