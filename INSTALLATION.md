# Installation Guide for Git Auto Commit (GAC)

## Overview

Git Auto Commit (GAC) is a powerful CLI tool that uses AI to generate meaningful commit messages based on your staged
changes. This guide will walk you through installation, configuration, and getting started.

## Prerequisites

- Python 3.10+
- pip or pipx
- Git 2.x
- An API key from a supported AI provider (optional)

## Installation Methods

### 1. Recommended: Install with pipx

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install GAC
pipx install gac
```

### 2. Install with pip

```bash
# Standard installation
pip install gac

# User installation (recommended if not using virtual environments)
pip install --user gac
```

### 3. Install from Source

```bash
# Clone the repository
git clone https://github.com/cellwebb/gac.git
cd gac

# Install in development mode
pip install -e .
```

## Quick Start

1. Stage your changes:

```bash
git add .
```

2. Generate a commit message:

```bash
gac
```

## Configuration

### AI Provider Setup

GAC supports multiple AI providers:

#### Anthropic Claude (Recommended)

1. Register at [console.anthropic.com](https://console.anthropic.com/)
2. Create an API key
3. Set the environment variable:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

#### Other Providers

- OpenAI: Set `OPENAI_API_KEY`
- Groq: Set `GROQ_API_KEY`
- Mistral: Set `MISTRAL_API_KEY`

### Configuration Locations

GAC loads configuration from multiple locations with the following precedence (highest to lowest):

1. Environment variables (set in your terminal session)
2. Project configuration (`.gac.env` in your current directory)
3. User configuration (`.gac.env` in your home directory)
4. Package configuration (installed with the module)
5. Default built-in values

This multi-level approach allows:

- Shared team settings in the package configuration
- Personal preferences in your home directory
- Project-specific overrides in each repository

### Manual Configuration

To configure GAC, create a `.gac.env` file in one of these locations:

```bash
# Create in your home directory (recommended)
echo 'GAC_MODEL=anthropic:claude-3-5-haiku-latest' > ~/.gac.env

# Or in your project directory
echo 'GAC_MODEL=anthropic:claude-3-5-haiku-latest' > .gac.env
```

You can also add your API key and other settings:

```bash
# Add to your existing .gac.env file
echo 'ANTHROPIC_API_KEY=your_key_here' >> ~/.gac.env
```

### Environment Variables

You can also configure GAC directly using environment variables:

```bash
# Model selection (required)
export GAC_MODEL=anthropic:claude-3-5-haiku-latest

# Optional settings
export GAC_USE_FORMATTING=true
export GAC_MAX_OUTPUT_TOKENS=512
export GAC_WARNING_LIMIT_INPUT_TOKENS=16000
export GAC_TEMPERATURE=0.7
```

## Configuration File Precedence

GAC uses a multi-level configuration system with a clear hierarchy of configuration sources. The configuration is loaded
in the following order of precedence (from highest to lowest):

1. **Command-line Arguments** (Highest Priority)

   - Directly passed arguments override all other configuration sources
   - Example: `gac -m anthropic:claude-3-5-haiku-latest`

2. **Project-level Configuration** (`.gac.env`)

   - Located in the current project's root directory
   - Applies only to the specific project
   - Overrides user-level and package-level configurations

3. **User-level Configuration** (`~/.gac.env`)

   - Located in the user's home directory
   - Applies to all projects for the current user
   - Overrides package-level configurations

4. **Package-level Configuration** (`config.env`)

   - Included with the GAC package installation
   - Provides default fallback configurations
   - Lowest priority configuration source

5. **Built-in Default Values** (Lowest Priority)
   - Hardcoded default settings within the application
   - Used only if no other configuration is specified

### Configuration Resolution Example

```bash
# Command-line argument takes highest priority
gac -m anthropic:claude-3-5-haiku-latest

# Project .gac.env (highest priority after CLI)
# /path/to/project/.gac.env
GAC_MODEL=openai:gpt-4
GAC_TEMPERATURE=0.7

# User-level ~/.gac.env
GAC_MODEL=groq:llama-3
GAC_API_KEY=user_api_key

# Package-level config.env
GAC_MODEL=anthropic:claude-3-5-haiku-latest
```

In this example:

- The CLI argument `anthropic:claude-3-5-haiku-latest` would be used
- If no CLI model is specified, the project's `openai:gpt-4` would be used
- Without a project config, the user-level `groq:llama-3` would be used
- If no other configuration is found, the package-level default is used

### Best Practices

- Use project-level `.gac.env` for project-specific configurations
- Use user-level `~/.gac.env` for personal default settings
- Keep sensitive information like API keys out of version control
- Use environment variables for dynamic or sensitive configurations

### Troubleshooting

- Use `gac --verbose` to see detailed configuration loading information
- Check that configuration files have correct permissions
- Ensure configuration files are valid and follow the correct format

## Advanced Usage

### Local Model Support (Ollama)

1. Install [Ollama](https://ollama.com/)
2. Pull a model:

```bash
ollama pull llama3
```

3. Use with GAC:

```bash
gac -m ollama:llama3
```

### Command-Line Options

```bash
# Stage all changes and commit
gac -a

# Use a specific model
gac -m openai:gpt-4o-mini

# Generate one-line commit message
gac -o

# Provide context hint
gac -h "Fix authentication bug"
```

## Troubleshooting

### Common Issues

- **API Key Problems**: Verify your API key and provider configuration
- **Model Unavailability**: Check model support and accessibility
- **Formatting Errors**: Ensure required formatters are installed

### Debugging

```bash
# Enable debug logging
gac --log-level=DEBUG

# Show prompt sent to AI
gac --show-prompt
```

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for information on contributing to GAC.

## License

GAC is released under the MIT License. See [LICENSE.txt](LICENSE.txt) for details.
