<!-- markdownlint-disable MD029-->

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
- Caches responses to improve performance and reduce API calls
- Interactive prompts for commit and push actions
- Supports various flags for different workflows

## Installation

```console
pipx install gac
```

## Configuration

### Interactive Configuration Wizard

Git Auto Commit provides an interactive configuration wizard to help you set up your preferred AI provider and model:

```bash
gac --config-wizard
```

The wizard will guide you through:

- Selecting an AI provider (Anthropic, OpenAI, Groq, Mistral)
- Choosing a specific model
- Configuring code formatting preferences

### Manual Configuration

You can also configure GAC using environment variables:

- `GAC_MODEL`: Full model specification (e.g., `anthropic:claude-3-5-haiku-latest`)
- `GAC_PROVIDER`: AI provider (e.g., `anthropic`)
- `GAC_MODEL_NAME`: Specific model name (e.g., `claude-3-5-haiku-latest`)
- `GAC_USE_FORMATTING`: Enable/disable code formatting (`true`/`false`)

Example:

```bash
export GAC_MODEL=anthropic:claude-3-5-haiku-latest
export GAC_USE_FORMATTING=true
gac
```

### Environment Variables

The following environment variables can be used to configure gac:

| Variable                         | Description                                      | Default                             | Required            |
| -------------------------------- | ------------------------------------------------ | ----------------------------------- | ------------------- |
| `ANTHROPIC_API_KEY`              | API key for Anthropic Claude                     | -                                   | Yes (for Anthropic) |
| `OPENAI_API_KEY`                 | API key for OpenAI models                        | -                                   | Yes (for OpenAI)    |
| `GROQ_API_KEY`                   | API key for Groq models                          | -                                   | Yes (for Groq)      |
| `MISTRAL_API_KEY`                | API key for Mistral models                       | -                                   | Yes (for Mistral)   |
| `GAC_MODEL`                      | Fully qualified model string (provider:model)    | `anthropic:claude-3-5-haiku-latest` | No                  |
| `GAC_USE_FORMATTING`             | Enable/disable code formatting (true/false)      | `true`                              | No                  |
| `GAC_MAX_OUTPUT_TOKENS`          | Maximum tokens in model output                   | `512`                               | No                  |
| `GAC_WARNING LIMIT_INPUT_TOKENS` | Maximum tokens in input prompt                   | `1000`                              | No                  |
| `GAC_LOG_LEVEL`                  | Set logging verbosity (DEBUG/INFO/WARNING/ERROR) | `INFO`                              | No                  |

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

| Provider    | Default Model                     | Description                                             |
| ----------- | --------------------------------- | ------------------------------------------------------- |
| `anthropic` | `claude-3-5-haiku-latest`         | Latest Claude model with enhanced context understanding |
| `openai`    | `gpt-4o-mini`                     | Optimized version of GPT-4 for commit messages          |
| `groq`      | `llama3-70b-8192`                 | Large Llama 3 model with 8192 context window            |
| `mistral`   | `mistral-large-latest`            | Latest Mistral large model                              |
| `aws`       | `meta.llama3-1-70b-instruct-v1:0` | AWS-hosted Llama 3 model                                |
| `azure`     | `gpt-4o-mini`                     | Azure-hosted GPT-4 optimized model                      |
| `google`    | `gemini-2.0-flash`                | Latest Gemini model with flash attention                |
| `ollama`    | `llama3.2`                        | Local Llama 3 model hosted through Ollama               |

### Using Local Models with Ollama

You can use locally-hosted models with Ollama:

1. Install Ollama from [https://ollama.com](https://ollama.com)
2. Start the Ollama service
3. Pull a model:
   ```bash
   ollama pull llama3.2
   ```
4. Use the model with gac:
   ```bash
   gac --model=ollama:llama3.2
   ```

To list available local models:

```bash
gac --local-models
```

**Note:** Using local models generally results in faster response times but may produce less refined commit messages than cloud-based models. For best results with local models, consider using the `--hint` option to provide additional context.

### Token Limits

You can adjust the token limits for both input and output:

```bash
# Increase output token limit
export GAC_MAX_OUTPUT_TOKENS=1024

# Increase input token limit (for larger diffs)
export GAC_WARNING_LIMIT_INPUT_TOKENS=24000
```

**Note:** The input token limit should be set based on your model's maximum context window size. Exceeding this limit may result in truncated diffs being sent to the model. The default token limit is 16000.

### Code Formatting

Code formatting is enabled by default. It uses `black` and `isort` to format Python files before committing. You can disable it if needed:

```bash
export GAC_USE_FORMATTING=false
```

This is useful if you're working on a project that uses different formatting tools or if you want to commit without formatting.

### Logging Control

GAC provides flexible logging control to adjust the verbosity of output. You can set the logging level in two ways:

1. Using command-line flags:

```bash
# Detailed debug logging
gac --DEBUG

# Default information level
gac --INFO

# Only show warnings
gac --WARNING

# Only show errors
gac --ERROR
```

2. Using the environment variable:

```bash
# Set to any of: DEBUG, INFO, WARNING, ERROR
export GAC_LOG_LEVEL=DEBUG
gac
```

The logging levels control what information is displayed:

- **DEBUG**: Detailed information for debugging and troubleshooting
- **INFO** (default): General information about the commit process
- **WARNING**: Only show warnings and more severe issues
- **ERROR**: Only show error messages

Use `--DEBUG` when you need to troubleshoot issues with API connections or unexpected behavior.

### Caching

GAC implements caching to improve performance and reduce API calls. The cache stores:

- LLM responses for similar diffs
- Git operations results
- Project descriptions

By default, the cache is stored in `~/.gac_cache/` and entries expire after 24 hours for LLM responses and 5 minutes for git operations.

You can control caching behavior with these command-line options:

```bash
# Skip cache and force fresh API calls
gac --no-cache

# Clear all cached data before running
gac --clear-cache
```

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

| Option               | Description                                        | Example                                  |
| -------------------- | -------------------------------------------------- | ---------------------------------------- |
| `--test, -t`         | Run in test mode with example commit messages      | `gac --test`                             |
| `--force, -f`        | Skip all prompts (auto-yes)                        | `gac -f`                                 |
| `--add-all, -a`      | Stage all changes before committing                | `gac -a`                                 |
| `--no-format`        | Disable automatic code formatting                  | `gac --no-format`                        |
| `--model, -m`        | Specify model to use (overrides GAC_MODEL)         | `gac --model=openai:gpt-4o`              |
| `--one-liner, -o`    | Generate one-line commit messages                  | `gac --one-liner`                        |
| `--show-prompt, -s`  | Show the prompt sent to the LLM                    | `gac --show-prompt`                      |
| `--hint, -h`         | Provide additional context for the commit message  | `gac --hint="This is a breaking change"` |
| `--conventional, -c` | Generate commit messages using conventional format | `gac --conventional`                     |
| `--no-cache`         | Skip cache and force fresh API calls               | `gac --no-cache`                         |
| `--clear-cache`      | Clear all cached data before running               | `gac --clear-cache`                      |
| `--DEBUG`            | Set logging level to DEBUG                         | `gac --DEBUG`                            |
| `--INFO`             | Set logging level to INFO (default)                | `gac --INFO`                             |
| `--WARNING`          | Set logging level to WARNING                       | `gac --WARNING`                          |
| `--ERROR`            | Set logging level to ERROR                         | `gac --ERROR`                            |

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

7. Conventional commit format:

```bash
gac --conventional
```

8. Force fresh API calls (skip cache):

```bash
gac --no-cache
```

### Best Practices

1. Always stage your changes before running `gac`
2. Use the `--hint` option to provide important context about your changes
3. Consider using `--one-liner` for smaller, focused commits
4. Use `--test` to preview commit messages before committing
5. If working on a project with specific formatting requirements, use `--no-format`
6. Use the cache to improve performance unless you need fresh responses

## Project Structure

```plaintext
gac/
├── src/
│   └── gac/
│       ├── __init__.py
│       ├── core.py
│       ├── ai_utils.py
│       ├── git.py
│       ├── cache.py
│       ├── config.py
│       ├── constants.py
│       ├── utils.py
│       └── formatting/
│           └── ... formatting modules ...
├── tests/
├── .gitignore
├── LICENSE.txt
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
└── pyproject.toml
```

## For Developers

### Testing

When running tests, GAC automatically sets a test mode environment variable to prevent real git commands from affecting your repository. This is important when testing functionality that interacts with git.

The test mode is controlled in two ways:

1. Environment variable:

```bash
# Set this to prevent real git commands from running
export GAC_TEST_MODE=1
```

2. Function parameter:

```python
# Pass test_mode=True to simulate git commands
from gac.utils import run_subprocess
result = run_subprocess(["git", "add", "."], test_mode=True)
```

When test mode is active, all git commands are intercepted and return simulated responses instead of executing real commands. This ensures tests don't accidentally modify your git repository.

### Contributing

Contributions are welcome! If you'd like to contribute to GAC, please:

1. Fork the repository
2. Create a new branch for your feature
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

Before submitting your PR, please make sure to run the test suite:

```bash
pytest
```

## License

MIT
