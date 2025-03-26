# Installation Guide

This guide provides instructions for installing and configuring GAC (Git Auto Commit) with support for multiple AI providers.

## Quick Start

1. Install GAC:

   ```bash
   pipx install gac
   ```

2. Set up at least one AI provider (Anthropic Claude is the default):

   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

3. Start using GAC:

   ```bash
   # Stage your changes
   git add .

   # Generate and apply a commit message
   gac
   ```

## Installation Methods

### Recommended: Install with pipx

[pipx](https://pypa.github.io/pipx/) installs the package in an isolated environment while making the CLI commands globally available.

1. Install pipx if you don't have it:

   ```bash
   # On macOS
   brew install pipx
   pipx ensurepath

   # On Ubuntu/Debian
   sudo apt update
   sudo apt install python3-pip python3-venv
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath

   # On Windows
   pip install pipx
   pipx ensurepath
   ```

2. Install GAC:

   ```bash
   pipx install gac
   ```

3. Verify installation:

   ```bash
   gac --help
   ```

### Alternative: Install with pip

```bash
# Standard installation
pip install gac

# Or user installation
pip install --user gac
```

### Install from Source

For developers or to get the latest changes:

```bash
# Clone the repository
git clone https://github.com/cellwebb/gac.git
cd gac

# Install in development mode
pip install -e .
```

## AI Provider Setup

GAC supports multiple AI providers. You need to set up at least one:

### Anthropic Claude (Default)

1. Register at [console.anthropic.com](https://console.anthropic.com/)
2. Create an API key and set it:

   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

### OpenAI (GPT-4, GPT-3.5)

1. Register at [platform.openai.com](https://platform.openai.com/)
2. Create an API key and set it:

   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

### Groq

1. Register at [console.groq.com](https://console.groq.com/)
2. Create an API key and set it:

   ```bash
   export GROQ_API_KEY=your_key_here
   ```

### Mistral

1. Register at [console.mistral.ai](https://console.mistral.ai/)
2. Create an API key and set it:

   ```bash
   export MISTRAL_API_KEY=your_key_here
   ```

### Other Providers

For other providers like AWS Bedrock, Azure, or Google, see the documentation for each provider in the `.env.example` file.

## Configuration

### Using Environment Variables

Add your configuration to your shell profile (e.g., `~/.bashrc` or `~/.zshrc`):

```bash
# AI Provider Keys
export ANTHROPIC_API_KEY=your_api_key_here
# export OPENAI_API_KEY=your_api_key_here
# export GROQ_API_KEY=your_api_key_here
# export MISTRAL_API_KEY=your_api_key_here

# GAC Configuration
export GAC_PROVIDER=anthropic  # Choose: anthropic, openai, groq, mistral, aws
# export GAC_MODEL_NAME=claude-3-haiku  # Model name for the selected provider
# export GAC_MODEL=openai:gpt-4o  # Or set a fully qualified model (overrides provider and model name)
# export GAC_USE_FORMATTING=true  # Whether to use black and isort for Python files
# export GAC_MAX_TOKENS=8192  # Maximum output tokens
```

### Using .env Files

Alternatively, create a `.env` file in your project directory with the same variables. This is useful for project-specific configurations.

### Using Command-Line Options

Override the model for a single run:

```bash
gac -m openai:gpt-4o
```

## Basic Usage

1. Stage your changes:

   ```bash
   git add <files>
   ```

2. Generate and apply a commit message:

   ```bash
   gac
   ```

3. Additional options:

   ```bash
   # Stage all changes and commit
   gac -a

   # Skip user confirmation
   gac -f

   # Skip code formatting
   gac -nf

   # Use a specific model
   gac -m groq:llama3-70b-8192
   ```

## Troubleshooting

### Common Issues

1. **API Key Not Recognized**

   If you get errors about missing API keys, ensure you've:

   - Exported the correct environment variable
   - Restarted your terminal session after adding to your profile
   - Checked for typos in your API key

2. **Command Not Found**

   If the `gac` command isn't found:

   - Ensure the Python bin directory is in your PATH
   - Try installing with `pipx` instead of `pip`
   - For pip installations, you might need to add `~/.local/bin` to your PATH:

     ```bash
     export PATH="$HOME/.local/bin:$PATH"
     ```

3. **Dependency Errors**

   If you encounter dependency errors:

   ```bash
   pip install --upgrade 'gac[all]'
   ```

4. **Model Not Found**

   If you get errors about models not being found:

   - Check that you've specified the correct model ID
   - Verify that your API key has access to the requested model
   - Try using a different model from the same provider

### Getting Help

If you continue to experience issues:

1. Run GAC in verbose mode for more information:

   ```bash
   gac -v
   ```

2. Check the [GitHub issues](https://github.com/cellwebb/gac/issues) for similar problems and solutions

3. Open a new issue with the error details and steps to reproduce
