# gac (Git Auto Commit)

[![Tests](https://github.com/cellwebb/gac/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/gac/actions/workflows/ci.yml)
[![Code Coverage](https://codecov.io/gh/cellwebb/gac/graph/badge.svg?token=WXOSX7R2JH)](https://codecov.io/gh/cellwebb/gac)
[![PyPI - Version](https://img.shields.io/pypi/v/gac.svg)](https://pypi.org/project/gac)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gac.svg)](https://pypi.org/project/gac)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool (pronounced like "gak") that uses large language models to generate meaningful commit messages based on your staged changes.

## Features

- Automatically generates meaningful commit messages using various LLM providers
- Supports multiple AI providers (Anthropic Claude, OpenAI, Groq, Mistral, and more)
- Formats Python files with `black` and `isort` before committing
- Interactive prompts for commit and push actions
- Supports various flags for different workflows

## Installation

```console
pipx install gac
```

## Configuration

### API Keys

Set up your API keys for the provider you want to use:

```console
# For Anthropic Claude (default)
export ANTHROPIC_API_KEY=your_api_key_here

# For OpenAI
export OPENAI_API_KEY=your_api_key_here

# For Groq
export GROQ_API_KEY=your_api_key_here

# For Mistral
export MISTRAL_API_KEY=your_api_key_here
```

For permanent configuration, add this to your shell profile (~/.zshrc, ~/.bashrc, etc.)

### Provider Configuration

You can specify which LLM provider and model to use:

```console
# Set provider (anthropic, openai, groq, mistral, aws, etc.)
export GAC_PROVIDER=anthropic

# Optionally, set a specific model name for the provider
export GAC_MODEL_NAME=claude-3-5-sonnet-20240620

# Or set a fully qualified model
export GAC_MODEL=openai:gpt-4o
```

## Usage

### Basic Usage

Stage your changes as usual with git:

```console
git add <files>
```

Then use `gac` to commit:

```console
gac
```

### Command Line Options

- `--test`: Run in test mode with example commit messages
- `--force, -f`: Skip all prompts (auto-yes)
- `--add-all, -a`: Stage all changes before committing
- `--no-format, -nf`: Disable automatic code formatting

Example:

```console
# Stage and commit all changes without prompts
gac -f -a
```

## Project Structure

```plaintext
gac/
├── src/
│   └── gac/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── tests/
├── .gitignore
├── LICENSE.txt
├── README.md
└── pyproject.toml
```

## Contributing

For development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT
