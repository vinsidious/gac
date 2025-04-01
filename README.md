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

Enable detailed logging:

```bash
# Debug level logging
gac --DEBUG

# Show the prompt sent to the AI
gac --show-prompt

# Show the complete prompt with diff
gac --show-prompt-full
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
