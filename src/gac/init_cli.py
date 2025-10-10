"""CLI for initializing gac configuration interactively."""

from pathlib import Path

import click
import questionary
from dotenv import set_key

GAC_ENV_PATH = Path.home() / ".gac.env"


@click.command()
def init() -> None:
    """Interactively set up $HOME/.gac.env for gac."""
    click.echo("Welcome to gac initialization!\n")
    if GAC_ENV_PATH.exists():
        click.echo(f"$HOME/.gac.env already exists at {GAC_ENV_PATH}. Values will be updated.")
    else:
        GAC_ENV_PATH.touch()
        click.echo(f"Created $HOME/.gac.env at {GAC_ENV_PATH}.")

    providers = [
        ("Anthropic", "claude-3-5-haiku-latest"),
        ("Cerebras", "qwen-3-coder-480b"),
        ("Gemini", "gemini-2.5-flash"),
        ("Groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
        ("LM Studio", "deepseek-r1-distill-qwen-7b"),
        ("Ollama", "gemma3"),
        ("OpenAI", "gpt-4.1-mini"),
        ("OpenRouter", "openrouter/auto"),
        ("Z.AI", "glm-4.5-air"),
        ("Z.AI Coding", "glm-4.6"),
    ]
    provider_names = [p[0] for p in providers]
    provider = questionary.select("Select your provider:", choices=provider_names).ask()
    if not provider:
        click.echo("Provider selection cancelled. Exiting.")
        return
    provider_key = provider.lower().replace(".", "").replace(" ", "-")
    model_suggestion = dict(providers)[provider]
    model = questionary.text(f"Enter the model (default: {model_suggestion}):", default=model_suggestion).ask()
    model_to_save = model.strip() if model.strip() else model_suggestion
    set_key(str(GAC_ENV_PATH), "GAC_MODEL", f"{provider_key}:{model_to_save}")
    click.echo(f"Set GAC_MODEL={provider_key}:{model_to_save}")

    api_key = questionary.password("Enter your API key (input hidden, can be set later):").ask()
    if api_key:
        # Z.AI and Z.AI Coding both use the same API key
        api_key_name = "ZAI_API_KEY" if provider_key in ["zai", "zai-coding"] else f"{provider_key.upper()}_API_KEY"
        set_key(str(GAC_ENV_PATH), api_key_name, api_key)
        click.echo(f"Set {api_key_name} (hidden)")

    click.echo(f"\ngac environment setup complete. You can edit {GAC_ENV_PATH} to update values later.")
