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

2. Configure hatch to use a local virtual environment:

   Add this to your `pyproject.toml`:

   ```toml
   [tool.hatch.env]
   path = "venv"
   ```

   This will create the virtual environment in the `venv/` directory at your project root instead of hatch's default location.

3. Create and activate a development environment:

   ```console
   # Create a new environment
   hatch env create

   # Activate the environment
   hatch shell
   ```

4. Install in development mode:

   ```console
   # Install with development dependencies
   pip install -e ".[dev]"
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

- Use the local `venv` Python interpreter
- Configure test discovery with pytest
- Set up code formatting with black
- Hide common Python cache directories

If you're using VSCode, these settings will be automatically applied when you open the project.

### Environment Management

```console
# Create a new environment
hatch env create

# Activate the environment
hatch shell

# List all environments
hatch env show

# Run a command in the environment without activating
hatch run <command>
```

### Testing and Linting

```console
# Run tests
hatch run test

# Run tests with coverage
hatch run test-cov

# Format code
hatch run format

# Run linters
hatch run lint
```

### Building and Publishing

```console
# Build the package
hatch build

# Check build
hatch clean
hatch build

# Publish to PyPI (maintainers only)
hatch publish
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
4. Run tests and linting: `hatch run test && hatch run lint`
5. Submit a pull request

## License

`gac` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
