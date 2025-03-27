#!/usr/bin/env python3
"""
Examples of using GAC with multiple AI providers.

This script demonstrates how to use different providers with GAC through:
1. Environment variables
2. Command-line options
3. Direct API calls

Run this script to see examples of different providers in action.
"""

import os
import subprocess
import sys
from typing import List

from dotenv import load_dotenv

# Add the src directory to the Python path for direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gac.config import PROVIDER_MODELS, get_config  # noqa: E402
from gac.utils import chat, count_tokens  # noqa: E402

# Load environment variables from .env file if it exists
load_dotenv()


def display_header(title: str) -> None:
    """Display a formatted header for each example."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def show_available_providers() -> None:
    """Show information about available providers and default models."""
    display_header("Available Providers and Default Models")

    print(f"{'Provider':<15} | {'Default Model':<40}")
    print("-" * 15 + "-+-" + "-" * 40)

    for provider, model in PROVIDER_MODELS.items():
        print(f"{provider:<15} | {model:<40}")


def check_api_keys() -> List[str]:
    """Check which provider API keys are set and return a list of available providers."""
    available_providers = []

    provider_keys = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "aws": "AWS_ACCESS_KEY_ID",  # AWS needs more than just this key
        "azure": "AZURE_API_KEY",
        "google": "GOOGLE_APPLICATION_CREDENTIALS",
    }

    display_header("Checking Available API Keys")

    for provider, env_var in provider_keys.items():
        if os.environ.get(env_var):
            available_providers.append(provider)
            print(f"✅ {provider:<15} | API key found")
        else:
            print(f"❌ {provider:<15} | API key not found")

    return available_providers


def demonstrate_environment_variables(provider: str) -> None:
    """Demonstrate setting provider via environment variables."""
    display_header(f"Setting Provider via Environment Variables ({provider})")

    # Set environment variables
    os.environ["GAC_PROVIDER"] = provider

    # Get config to see the effect
    config = get_config()

    # Display configuration
    print(f"Environment Variable: GAC_PROVIDER={provider}")
    print(f"Resulting model: {config['model']}")


def demonstrate_command_line() -> None:
    """Demonstrate using command-line options to specify a model."""
    display_header("Setting Model via Command Line")

    # List of examples to show
    examples = [
        "gac -m anthropic:claude-3-5-haiku",
        "gac -m openai:gpt-4o-mini",
        "gac -m groq:gemma-7b-it",
        "gac -m mistral:mistral-small-latest",
    ]

    for example in examples:
        print(f"Command: {example}")

    print("\nThese commands will override any environment variables for a single run.")


def demonstrate_direct_api_call(provider: str) -> None:
    """Demonstrate direct API calls to different providers."""
    display_header(f"Direct API Call Example ({provider})")

    if provider not in PROVIDER_MODELS:
        print(f"Provider {provider} not found in PROVIDER_MODELS.")
        return

    # Construct fully qualified model ID
    model = f"{provider}:{PROVIDER_MODELS[provider]}"

    # Sample message for a simple commit message generation
    messages = [
        {
            "role": "user",
            "content": "Suggest a commit message for adding multi-provider support to a CLI tool.",
        }
    ]

    print(f"Making a direct call to {model}...")

    try:
        # First check token count
        token_count = count_tokens(messages[0]["content"], model)
        print(f"Token count for prompt: {token_count}")

        # Make the API call
        response = chat(
            messages=messages,
            model=model,
            temperature=0.7,
            system="You are a helpful assistant specializing in writing concise git commit messages. Keep your response to a single commit message.",  # noqa: E501
        )

        print("\nResponse from the API:")
        print("-" * 40)
        print(response)
        print("-" * 40)

    except Exception as e:
        print(f"Error making API call: {e}")


def run_gac_example(provider: str) -> None:
    """Run GAC from command line with a specific provider."""
    display_header(f"Running GAC Command Line with {provider}")

    # Check if in a git repository
    try:
        subprocess.run(
            ["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
    except subprocess.CalledProcessError:
        print("Not in a git repository. This example requires being in a git repository.")
        return

    # Construct model string
    model = f"{provider}:{PROVIDER_MODELS[provider]}"

    # Show command
    command = f"gac -t -m {model}"
    print(f"Command: {command}")

    # Execute GAC in test mode
    print("\nRunning GAC in test mode...")
    try:
        subprocess.run(["gac", "-t", "-m", model], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running GAC: {e}")
    except FileNotFoundError:
        print("GAC command not found. Make sure GAC is installed and in your PATH.")


def main() -> None:
    """Run all examples."""
    print("GAC Multi-Provider Examples")
    print("==========================")

    # Show available providers
    show_available_providers()

    # Check which providers are available based on API keys
    available_providers = check_api_keys()

    if not available_providers:
        print("\nNo API keys found. Please set API keys in your environment or .env file.")
        print("Example .env file:\n")
        print("ANTHROPIC_API_KEY=your_key_here")
        print("OPENAI_API_KEY=your_key_here")
        print("GROQ_API_KEY=your_key_here")
        print("MISTRAL_API_KEY=your_key_here")
        return

    # Use the first available provider for examples
    example_provider = available_providers[0]

    # Show examples
    demonstrate_environment_variables(example_provider)
    demonstrate_command_line()

    # Ask if user wants to run API examples
    response = input("\nDo you want to run a direct API call example? (y/n): ")
    if response.lower().startswith("y"):
        # Let user select a provider
        for i, provider in enumerate(available_providers):
            print(f"{i + 1}. {provider}")

        choice = input(f"Select a provider (1-{len(available_providers)}): ")
        try:
            provider_index = int(choice) - 1
            if 0 <= provider_index < len(available_providers):
                demonstrate_direct_api_call(available_providers[provider_index])
        except ValueError:
            print("Invalid choice.")

    # Ask if user wants to run GAC command-line example
    response = input("\nDo you want to run GAC from the command line? (y/n): ")
    if response.lower().startswith("y"):
        # Let user select a provider
        for i, provider in enumerate(available_providers):
            print(f"{i + 1}. {provider}")

        choice = input(f"Select a provider (1-{len(available_providers)}): ")
        try:
            provider_index = int(choice) - 1
            if 0 <= provider_index < len(available_providers):
                run_gac_example(available_providers[provider_index])
        except ValueError:
            print("Invalid choice.")

    print("\nExamples completed. For more information, see the README.md file.")


if __name__ == "__main__":
    main()
