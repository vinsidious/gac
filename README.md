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

### For Users

The recommended way to install `gac` is using `pipx`:

```console
pipx install gac
```

### For Developers

1. Clone the repository:

   ```console
   git clone https://github.com/cellwebb/gac.git
   cd gac
   ```

2. Set up with uv:

   ```console
   # Create a virtual environment and install dependencies
   make setup

   # Alternatively, you can use uv directly:
   uv venv
   uv pip install -e ".[dev]"
   ```

3. Activate the virtual environment:

   ```console
   source .venv/bin/activate
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

## Development Commands

Here are common commands you'll need during development:

### VSCode Integration

The repository includes VSCode settings that:

- Use the local virtual environment Python interpreter
- Configure test discovery with pytest
- Set up code formatting with black
- Hide common Python cache directories

If you're using VSCode, these settings will be automatically applied when you open the project.

### Development Tasks with Make

The project includes a Makefile for common development tasks:

```console
# Set up development environment
make setup

# Install package
make install

# Install with dev dependencies
make install-dev

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Clean build artifacts
make clean
```

### Alternative: Direct uv commands

```console
# Create virtual environment
uv venv

# Install package with dev dependencies
uv pip install -e ".[dev]"

# Update dependencies
uv pip install -U -e ".[dev]"
```

### Testing and Linting

```console
# Run tests
pytest

# Run tests with coverage
pytest --cov

# Format code
black .
isort .

# Run linters
flake8 .
```

### Building and Publishing

```console
# Build the package
python -m build

# Check build
rm -rf dist/
python -m build

# Publish to PyPI (maintainers only)
python -m twine upload dist/*
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
├── venv/
├── .gitignore
├── LICENSE.txt
├── README.md
└── pyproject.toml
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and linting: `make test && make lint`
5. Submit a pull request

## License

`gac` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
