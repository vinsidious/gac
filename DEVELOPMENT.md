# Development Guide for GAC

This document contains instructions for developers who want to contribute to the GAC (Git Auto Commit) project.

## Getting Started

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

## Development Workflow

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

## Building and Publishing

```console
# Build the package
python -m build

# Check build
rm -rf dist/
python -m build

# Publish to PyPI (maintainers only)
python -m twine upload dist/*
```

## Version Management

The project uses `bump2version` for version management. You can bump the version using the following make commands:

```console
# Bump patch version (0.1.0 -> 0.1.1)
make bump-patch

# Bump minor version (0.1.0 -> 0.2.0)
make bump-minor

# Bump major version (0.1.0 -> 1.0.0)
make bump-major

# Bump to next alpha (0.1.0a1 -> 0.1.0a2)
make bump-alpha

# Bump to next beta (0.1.0b1 -> 0.1.0b2)
make bump-beta

# Bump to next release candidate (0.1.0rc1 -> 0.1.0rc2)
make bump-rc
```

After bumping the version, be sure to update the CHANGELOG.md file with your changes.

## Development Installation Options

If you want to make the `gac` command available during development without having to activate the virtual environment each time, you have several options:

### Option 1: Use pipx in development mode

This is a clean approach that keeps your development version isolated:

```bash
pipx install -e /path/to/your/gac/repo
```

This will install your package in editable mode using pipx, which creates an isolated environment but makes the command globally available. Any changes you make to your code will be immediately reflected when you run the command.

### Option 2: Create a development alias

You can add an alias to your shell profile (`.zshrc`, `.bashrc`, etc.) that points to your development version:

```bash
alias dev-gac="python /path/to/your/gac/repo/src/gac/core.py"
```

This would let you run `dev-gac` from anywhere, and it would use your current code.

### Option 3: Add a symbolic link to your PATH

1. First, make sure your script is executable:

   ```bash
   chmod +x /path/to/your/gac/repo/src/gac/core.py
   ```

2. Add a shebang line to the top of your core.py file if it doesn't have one:

   ```python
   #!/usr/bin/env python
   ```

3. Create a symbolic link in a directory that's in your PATH:

   ```bash
   ln -s /path/to/your/gac/repo/src/gac/core.py /usr/local/bin/dev-gac
   ```

## Project Structure

```plaintext
gac/
├── src/
│   └── gac/
│       ├── __init__.py
│       ├── __about__.py
│       ├── core.py
│       └── utils.py
├── tests/
├── .venv/
├── .gitignore
├── LICENSE.txt
├── README.md
├── DEVELOPMENT.md
├── CHANGELOG.md
└── pyproject.toml
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and linting: `make test && make lint`
5. Submit a pull request
