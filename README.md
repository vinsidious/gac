# gac (Git Auto Commit)

[![Tests](https://github.com/cellwebb/gac/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/gac/actions/workflows/ci.yml)
[![Code Coverage](https://codecov.io/gh/cellwebb/gac/graph/badge.svg?token=WXOSX7R2JH)](https://codecov.io/gh/cellwebb/gac)
[![PyPI - Version](https://img.shields.io/pypi/v/gac.svg)](https://pypi.org/project/gac)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gac.svg)](https://pypi.org/project/gac)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool (pronounced like "gak") that uses large language models to generate meaningful commit messages based on your staged changes. Built with functional programming principles for simplicity and maintainability.

## Features

- **Functional Design**: Emphasizes pure functions, immutability, and composability
- **Multiple AI Providers**: Supports Anthropic Claude, OpenAI, Groq, Mistral, and local models through Ollama
- **Code Formatting**: Automatically formats Python files with `black` and `isort` before committing
- **Smart Token Management**: Optimizes context usage for large diffs
- **Conventional Commits**: Generates commit messages following conventional commit format
- **Local Models**: Run fully locally with Ollama integration
- **Configurability**: Extensive environment variable and CLI options
- **Multi-Platform**: Works on macOS, Linux, and Windows

## Installation

```console
pipx install gac
```

For detailed installation instructions including alternative methods, see [INSTALLATION.md](INSTALLATION.md).

## Quick Start

### Basic Usage

```bash
# Stage your changes
git add .

# Generate and commit with AI
gac
```

### Command Options

```bash
# Add all changes and commit
gac -a

# Skip confirmation
gac -f

# Use a specific model
gac -m anthropic:claude-3-5-sonnet-20240620

# Generate one-line commit message
gac -o

# Provide a hint for context
gac -h "Fix login bug in auth system"

# Commit and push in one command
gac -p

# Skip code formatting
gac --no-format
```

## Configuration

### Using Environment Variables

```bash
# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Choose model
export GAC_MODEL=anthropic:claude-3-5-haiku-latest

# Disable formatting
export GAC_USE_FORMATTING=false

# Set token limits
export GAC_MAX_OUTPUT_TOKENS=1024
```

### Interactive Setup

Run the configuration wizard:

```bash
gac --config-wizard
```

## Using Local Models with Ollama

For privacy or offline use, integrate with [Ollama](https://ollama.com):

```bash
# Install Ollama
# See https://ollama.com for installation

# Start the Ollama service
ollama start

# Pull a model
ollama pull llama3.2

# Use with gac
gac -m ollama:llama3.2
```

List available local models:

```bash
gac models
```

## Debugging and Troubleshooting

### Common Issues

1. **API Key Issues**: If you see authentication errors, check that you've set the environment variables for your AI provider (e.g., `ANTHROPIC_API_KEY`).

2. **Model Selection**: If you see errors about unavailable models, check that:
   - You've spelled the model name correctly
   - You have access to the model specified
   - For Ollama models, check that Ollama is running with `ollama serve`
3. **Token Limits**: If you see truncated outputs, try:
   - Breaking up your changes into smaller commits
   - Using the `--hint` flag to provide more specific guidance

### Debugging

Enable debug logging to see detailed information about API calls and operations:

```bash
# Set log level to DEBUG
gac --log-level=DEBUG

# View detailed operations and use a local model
gac --log-level=DEBUG --model="ollama:llama3"

# Show the prompt sent to the AI
gac --show-prompt

# Show the complete prompt with diff
gac --show-prompt-full
```

### Common Error Codes

1. Error code **1**: General application error
2. Error code **2**: Configuration error (check your settings)
3. Error code **3**: Git error (check your repository state)
4. Error code **4**: AI provider error (check API keys and network)
5. Error code **5**: Code formatting error (check formatter installation)

### Fallback Options

If you're facing issues with AI providers:

1. **Use Local Models**: `gac --model="ollama:llama3"`
2. **Skip Formatting**: `gac --no-format`
3. **Manual Mode**: `gac --manual` to skip AI generation and provide your own message

## Developer API

For developers wanting to use GAC programmatically, we provide a functional API:

```python
from gac.git import commit_workflow

# Simple usage
result = commit_workflow(
    stage_all=True,
    format_files=True,
    one_liner=True,
    push=True
)

if result["success"]:
    print(f"Committed with message: {result['message']}")
else:
    print(f"Error: {result['error']}")

# Advanced usage with options dictionaries
from gac.git import create_commit_options, commit_changes_with_options

# Create options dictionary
options = create_commit_options(
    message=None,  # Use AI to generate message
    add_all=True,  # Stage all changes
    formatting=True,  # Format code
    model="anthropic:claude-3-5-haiku",  # Use specific model
    hint="Fix authorization bug",  # Provide context hint
    one_liner=False,  # Generate multi-line message
    show_prompt=True,  # Show the prompt sent to AI
    force=False,  # Require confirmation
    push=True  # Push after commit
)

# Execute commit with options
message = commit_changes_with_options(options)
```

## Architecture

GAC follows a functional programming approach organized around these core modules:

1. **CLI Interface** (`cli.py`): Command-line options and entry point
2. **Git Operations** (`git.py`): Pure functions for git commands and diff handling
3. **AI Integration** (`ai.py`): Interfaces with AI providers through aisuite
4. **Formatting** (`format.py`): Code formatting and linting
5. **Prompt Management** (`prompt.py`): Building and cleaning prompts
6. **Configuration** (`config.py`): Loading and validating settings

### Design Principles

- **Pure Functions**: Minimize side effects and make dependencies explicit
- **Composability**: Small, focused functions that can be combined
- **Immutability**: Avoid modifying state when possible
- **Explicit Dependencies**: No hidden requirements or global state
- **Simplified Error Handling**: Consistent error types and helpful messages

## For Developers

See [DEVELOPMENT.md](DEVELOPMENT.md) for:

- Setting up a development environment
- Development workflow
- Testing approach
- Contributing guidelines

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the project history and recent updates.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned improvements and upcoming features.

## License

MIT
