"""CLI for initializing gac configuration interactively."""

from pathlib import Path

import click
import questionary
from dotenv import set_key

GAC_ENV_PATH = Path.home() / ".gac.env"


def _prompt_required_text(prompt: str) -> str | None:
    """Prompt until a non-empty string is provided or the user cancels."""
    while True:
        response = questionary.text(prompt).ask()
        if response is None:
            return None
        value = response.strip()
        if value:
            return value
        click.echo("A value is required. Please try again.")


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
        ("Anthropic", "claude-haiku-4-5"),
        ("Cerebras", "qwen-3-coder-480b"),
        ("Chutes.ai", "zai-org/GLM-4.6-FP8"),
        ("Gemini", "gemini-2.5-flash"),
        ("Groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
        ("LM Studio", "gemma3"),
        ("Ollama", "gemma3"),
        ("OpenAI", "gpt-4.1-mini"),
        ("OpenRouter", "openrouter/auto"),
        ("Streamlake", ""),
        ("Synthetic", "hf:zai-org/GLM-4.6"),
        ("Z.AI", "glm-4.5-air"),
        ("Z.AI Coding", "glm-4.6"),
    ]
    provider_names = [p[0] for p in providers]
    provider = questionary.select("Select your provider:", choices=provider_names).ask()
    if not provider:
        click.echo("Provider selection cancelled. Exiting.")
        return
    provider_key = provider.lower().replace(".", "").replace(" ", "-").replace("syntheticnew", "synthetic")

    is_ollama = provider_key == "ollama"
    is_lmstudio = provider_key == "lm-studio"
    is_streamlake = provider_key == "streamlake"
    is_zai = provider_key in ("zai", "zai-coding")

    if is_streamlake:
        endpoint_id = _prompt_required_text("Enter the Streamlake inference endpoint ID (required):")
        if endpoint_id is None:
            click.echo("Streamlake configuration cancelled. Exiting.")
            return
        model_to_save = endpoint_id
    else:
        model_suggestion = dict(providers)[provider]
        model_prompt = f"Enter the model (default: {model_suggestion}):"
        model = questionary.text(model_prompt, default=model_suggestion).ask()
        if model is None:
            click.echo("Model entry cancelled. Exiting.")
            return
        model_to_save = model.strip() if model.strip() else model_suggestion

    set_key(str(GAC_ENV_PATH), "GAC_MODEL", f"{provider_key}:{model_to_save}")
    click.echo(f"Set GAC_MODEL={provider_key}:{model_to_save}")

    if is_ollama:
        url_default = "http://localhost:11434"
        url = questionary.text(f"Enter the Ollama API URL (default: {url_default}):", default=url_default).ask()
        if url is None:
            click.echo("Ollama URL entry cancelled. Exiting.")
            return
        url_to_save = url.strip() if url.strip() else url_default
        set_key(str(GAC_ENV_PATH), "OLLAMA_API_URL", url_to_save)
        click.echo(f"Set OLLAMA_API_URL={url_to_save}")
    elif is_lmstudio:
        url_default = "http://localhost:1234"
        url = questionary.text(f"Enter the LM Studio API URL (default: {url_default}):", default=url_default).ask()
        if url is None:
            click.echo("LM Studio URL entry cancelled. Exiting.")
            return
        url_to_save = url.strip() if url.strip() else url_default
        set_key(str(GAC_ENV_PATH), "LMSTUDIO_API_URL", url_to_save)
        click.echo(f"Set LMSTUDIO_API_URL={url_to_save}")

    api_key_prompt = "Enter your API key (input hidden, can be set later):"
    if is_ollama or is_lmstudio:
        click.echo(
            "This provider typically runs locally. API keys are optional unless your instance requires authentication."
        )
        api_key_prompt = "Enter your API key (optional, press Enter to skip):"

    api_key = questionary.password(api_key_prompt).ask()
    if api_key:
        if is_zai:
            api_key_name = "ZAI_API_KEY"
        else:
            api_key_name = f"{provider_key.upper()}_API_KEY"
        set_key(str(GAC_ENV_PATH), api_key_name, api_key)
        click.echo(f"Set {api_key_name} (hidden)")
    elif is_ollama or is_lmstudio:
        click.echo("Skipping API key. You can add one later if needed.")

    click.echo(f"\ngac environment setup complete. You can edit {GAC_ENV_PATH} to update values later.")
