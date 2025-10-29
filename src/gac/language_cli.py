"""CLI for selecting commit message language interactively."""

from pathlib import Path

import click
import questionary
from dotenv import set_key, unset_key

GAC_ENV_PATH = Path.home() / ".gac.env"


@click.command()
def language() -> None:
    """Set the language for commit messages interactively."""
    click.echo("Select a language for your commit messages:\n")

    # Languages in their native scripts
    languages = [
        ("English", "English"),
        ("Español", "Spanish"),
        ("Français", "French"),
        ("Deutsch", "German"),
        ("Italiano", "Italian"),
        ("Português", "Portuguese"),
        ("日本語", "Japanese"),
        ("한국어", "Korean"),
        ("中文", "Chinese"),
        ("Русский", "Russian"),
        ("العربية", "Arabic"),
        ("हिन्दी", "Hindi"),
        ("Nederlands", "Dutch"),
        ("Polski", "Polish"),
        ("Türkçe", "Turkish"),
        ("Svenska", "Swedish"),
        ("Norsk", "Norwegian"),
        ("Suomi", "Finnish"),
        ("Dansk", "Danish"),
        ("Ελληνικά", "Greek"),
        ("עברית", "Hebrew"),
        ("ไทย", "Thai"),
        ("Tiếng Việt", "Vietnamese"),
        ("Bahasa Indonesia", "Indonesian"),
        ("Custom", "Custom"),
    ]

    display_names = [lang[0] for lang in languages]
    selection = questionary.select(
        "Choose your language:", choices=display_names, use_shortcuts=True, use_arrow_keys=True
    ).ask()

    if not selection:
        click.echo("Language selection cancelled.")
        return

    # Ensure .gac.env exists
    if not GAC_ENV_PATH.exists():
        GAC_ENV_PATH.touch()
        click.echo(f"Created {GAC_ENV_PATH}")

    # Handle English (default) - remove the setting
    if selection == "English":
        try:
            unset_key(str(GAC_ENV_PATH), "GAC_LANGUAGE")
            click.echo("✓ Set language to English (default)")
            click.echo(f"  Removed GAC_LANGUAGE from {GAC_ENV_PATH}")
        except Exception:
            click.echo("✓ Set language to English (default)")
        return

    # Handle custom input
    if selection == "Custom":
        custom_language = questionary.text("Enter the language name (e.g., 'Spanish', 'Français', '日本語'):").ask()
        if not custom_language or not custom_language.strip():
            click.echo("No language entered. Cancelled.")
            return
        language_value = custom_language.strip()
    else:
        # Find the English name for the selected language
        language_value = next(lang[1] for lang in languages if lang[0] == selection)

    # Set the language in .gac.env
    set_key(str(GAC_ENV_PATH), "GAC_LANGUAGE", language_value)
    click.echo(f"✓ Set language to {selection}")
    click.echo(f"  GAC_LANGUAGE={language_value} in {GAC_ENV_PATH}")
    click.echo("\n  Note: Conventional commit prefixes (feat:, fix:, etc.) will remain in English.")
