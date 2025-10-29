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

    # Languages sorted by programmer population likelihood
    # Based on GitHub statistics and global developer demographics
    languages = [
        ("English", "English"),
        ("简体中文", "Simplified Chinese"),
        ("繁體中文", "Traditional Chinese"),
        ("日本語", "Japanese"),
        ("한국어", "Korean"),
        ("Español", "Spanish"),
        ("Português", "Portuguese"),
        ("Français", "French"),
        ("Deutsch", "German"),
        ("Русский", "Russian"),
        ("हिन्दी", "Hindi"),
        ("Italiano", "Italian"),
        ("Polski", "Polish"),
        ("Türkçe", "Turkish"),
        ("Nederlands", "Dutch"),
        ("Tiếng Việt", "Vietnamese"),
        ("ไทย", "Thai"),
        ("Bahasa Indonesia", "Indonesian"),
        ("Svenska", "Swedish"),
        ("العربية", "Arabic"),
        ("עברית", "Hebrew"),
        ("Ελληνικά", "Greek"),
        ("Dansk", "Danish"),
        ("Norsk", "Norwegian"),
        ("Suomi", "Finnish"),
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

    # Ask about prefix translation
    click.echo()  # Blank line for spacing
    prefix_choice = questionary.select(
        "How should conventional commit prefixes be handled?",
        choices=[
            "Keep prefixes in English (feat:, fix:, etc.)",
            f"Translate prefixes into {language_value}",
        ],
    ).ask()

    if not prefix_choice:
        click.echo("Prefix translation selection cancelled.")
        return

    translate_prefixes = prefix_choice.startswith("Translate prefixes")

    # Set the language and prefix translation preference in .gac.env
    set_key(str(GAC_ENV_PATH), "GAC_LANGUAGE", language_value)
    set_key(str(GAC_ENV_PATH), "GAC_TRANSLATE_PREFIXES", "true" if translate_prefixes else "false")

    click.echo(f"\n✓ Set language to {selection}")
    click.echo(f"  GAC_LANGUAGE={language_value}")
    if translate_prefixes:
        click.echo("  GAC_TRANSLATE_PREFIXES=true")
        click.echo("\n  Prefixes will be translated (e.g., 'corrección:' instead of 'fix:')")
    else:
        click.echo("  GAC_TRANSLATE_PREFIXES=false")
        click.echo(f"\n  Prefixes will remain in English (e.g., 'fix: <{language_value} description>')")
    click.echo(f"\n  Configuration saved to {GAC_ENV_PATH}")
