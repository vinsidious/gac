# gac (Git Auto Commit)

[![PyPI - Version](https://img.shields.io/pypi/v/gac.svg)](https://pypi.org/project/gac)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gac.svg)](https://pypi.org/project/gac)

A CLI tool (pronounced like "gak") that uses large language models to generate meaningful commit messages based on your staged changes.

## Features

- Automatically generates meaningful commit messages using Claude AI
- Formats Python files with `black` and `isort` before committing
- Interactive prompts for commit and push actions
- Supports various flags for different workflows

## Installation

```console
pipx install gac
```

## Configuration

1. Set up your Claude API key:

   ```console
   export CLAUDE_API_KEY=your_api_key_here
   ```

   For permanent configuration, add this to your shell profile (~/.zshrc, ~/.bashrc, etc.)

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
