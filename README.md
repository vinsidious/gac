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

### Environment Variables

The following environment variables can be used to configure gac:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | API key for Anthropic Claude | - | Yes (for Anthropic) |
| `OPENAI_API_KEY` | API key for OpenAI models | - | Yes (for OpenAI) |
| `GROQ_API_KEY` | API key for Groq models | - | Yes (for Groq) |
| `MISTRAL_API_KEY` | API key for Mistral models | - | Yes (for Mistral) |
| `GAC_MODEL` | Fully qualified model string (provider:model) | `anthropic:claude-3-5-haiku-latest` | No |
| `GAC_USE_FORMATTING` | Enable/disable code formatting (true/false) | `true` | No |
| `GAC_MAX_OUTPUT_TOKENS` | Maximum tokens in model output | `512` | No |
| `GAC_MAX_INPUT_TOKENS` | Maximum tokens in input prompt | `1000` | No |

### Model Selection

You can specify which LLM model to use in several ways:

1. Using `GAC_MODEL` (recommended):
```bash
export GAC_MODEL=anthropic:claude-3-5-haiku-latest
```

2. Using separate provider and model name:
```bash
export GAC_PROVIDER=anthropic
export GAC_MODEL_NAME=claude-3-5-haiku-latest
```

3. Using provider-specific environment variables:
```bash
export GAC_PROVIDER=anthropic
# Will use default model for provider
```

Available providers and their default models:

| Provider | Default Model | Description |
|----------|---------------|-------------|
| `anthropic` | `claude-3-5-haiku-latest` | Latest Claude model with enhanced context understanding |
| `openai` | `gpt-4o-mini` | Optimized version of GPT-4 for commit messages |
| `groq` | `llama3-70b-8192` | Large Llama 3 model with 8192 context window |
| `mistral` | `mistral-large-latest` | Latest Mistral large model |
| `aws` | `meta.llama3-1-70b-instruct-v1:0` | AWS-hosted Llama 3 model |
| `azure` | `gpt-4o-mini` | Azure-hosted GPT-4 optimized model |
| `google` | `gemini-2.0-flash` | Latest Gemini model with flash attention |

### Token Limits

You can adjust the token limits for both input and output:

```bash
# Increase output token limit
export GAC_MAX_OUTPUT_TOKENS=1024

# Increase input token limit (for larger diffs)
export GAC_MAX_INPUT_TOKENS=2048
```

**Note:** The input token limit should be set based on your model's maximum context window size. Exceeding this limit may result in truncated diffs being sent to the model.

### Code Formatting

Code formatting is enabled by default. It uses `black` and `isort` to format Python files before committing. You can disable it if needed:

```bash
export GAC_USE_FORMATTING=false
```

This is useful if you're working on a project that uses different formatting tools or if you want to commit without formatting.

## Usage

### Basic Usage

1. Stage your changes as usual with git:
```bash
git add <files>
```

2. Use `gac` to commit:
```bash
gac
```

### Command Line Options

```bash
gac [OPTIONS]
```

Available options:

| Option | Description | Example |
|--------|-------------|---------|
| `--test` | Run in test mode with example commit messages | `gac --test` |
| `--force, -f` | Skip all prompts (auto-yes) | `gac -f` |
| `--add-all, -a` | Stage all changes before committing | `gac -a` |
| `--no-format, -nf` | Disable automatic code formatting | `gac --no-format` |
| `--model` | Specify model to use (overrides GAC_MODEL) | `gac --model=openai:gpt-4o` |
| `--one-liner` | Generate one-line commit messages | `gac --one-liner` |
| `--show-prompt` | Show the prompt sent to the LLM | `gac --show-prompt` |
| `--hint` | Provide additional context for the commit message | `gac --hint="This is a breaking change"` |

### Common Workflows

1. Quick commit with all changes:
```bash
gac -f -a
```

2. Generate a one-line commit message:
```bash
gac --one-liner
```

3. Use a specific model:
```bash
gac --model=openai:gpt-4o
```

4. Provide additional context:
```bash
gac --hint="This is a breaking change"
```

5. Test the commit message without actually committing:
```bash
gac --test
```

6. View the prompt being sent to the LLM:
```bash
gac --show-prompt
```

### Best Practices

1. Always stage your changes before running `gac`
2. Use the `--hint` option to provide important context about your changes
3. Consider using `--one-liner` for smaller, focused commits
4. Use `--test` to preview commit messages before committing
5. If working on a project with specific formatting requirements, use `--no-format`

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
