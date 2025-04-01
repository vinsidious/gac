# Development Guide for GAC

This document contains instructions for developers who want to contribute to the GAC (Git Auto Commit) project, with a focus on functional programming principles.

## Functional Programming Philosophy

GAC follows these core functional programming principles:

1. **Pure Functions**: Functions should avoid side effects and have predictable outputs based solely on their inputs
2. **Immutability**: Data should not be modified after creation
3. **Composability**: Build complex operations from simple, reusable functions
4. **Explicit Dependencies**: Dependencies should be passed as arguments, not accessed from global state
5. **Error Handling**: Errors should be returned, not thrown (when possible)

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

## Architecture Overview

GAC uses a modular, function-based architecture:

```text
src/gac/
├── __init__.py       # Package exports
├── __about__.py      # Version info
├── ai.py             # AI model integration functions
├── cli.py            # Command-line interface
├── config.py         # Configuration handling
├── errors.py         # Error types and handling
├── format.py         # Code formatting utilities
├── git.py            # Git operations
├── prompt.py         # Prompt building and processing
└── utils.py          # General utilities
```

### Key Module Responsibilities

- **ai.py**: Handles provider integration, token counting, and prompt optimization
- **git.py**: Git operations with pure functions for getting diffs, staging, committing
- **format.py**: Code formatting for Python and other languages
- **prompt.py**: Building and cleaning prompts for AI models
- **config.py**: Configuration from environment variables and validation

## Development Best Practices

### Writing Functions

Follow these guidelines when writing or modifying functions:

```python
# Good: Pure function with explicit dependencies
def format_file(file_path: str, formatter_command: List[str]) -> bool:
    """Format a single file with the given formatter.

    Args:
        file_path: Path to the file to format
        formatter_command: Command to run the formatter

    Returns:
        True if formatting succeeded, False otherwise
    """
    # Implementation...

# Avoid: Function with implicit dependencies and side effects
def format_file(file_path: str) -> None:
    """Format a file with automatically detected formatter.

    Args:
        file_path: Path to the file to format
    """
    # Bad: Accessing global state
    command = FORMATTERS.get(get_file_type(file_path))
    # Bad: Side effects without return value
    subprocess.run(command)
```

### Testing

GAC uses pytest for testing. Follow these testing principles:

1. **Test Behavior, Not Implementation**: Focus on what functions do, not how
2. **Use Pure Function Testing**: Tests should be deterministic and isolated
3. **Minimize Mocking**: Only mock external dependencies when necessary
4. **Use Fixtures**: Create reusable test fixtures for common setup
5. **Property-Based Testing**: Consider using hypothesis for property testing

Example:

````python
# Good test: Tests behavior, not implementation
def test_clean_commit_message():
    # Given a message with backticks
    message = "```\nTest message\n```"

    # When cleaned
    result = clean_commit_message(message)

    # Then it should have conventional prefix and no backticks
    assert result == "chore: Test message"
````

### Testing Commands

When running tests:

```console
# Run all tests
make test

# Run tests with coverage
make coverage

# Run linting
make lint

# Format code
make format
```

## Development Tasks with Make

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

## Version Management

The project uses `bump-my-version` for version management:

```console
# Bump patch version (0.1.0 -> 0.1.1)
make bump-patch

# Bump minor version (0.1.0 -> 0.2.0)
make bump-minor

# Bump major version (0.1.0 -> 1.0.0)
make bump-major
```

After bumping the version, be sure to update the CHANGELOG.md file with your changes.

## Contributing

To contribute to GAC:

1. Fork the repository
2. Create a new branch for your feature or fix
3. Follow the functional programming principles
4. Write tests for your changes
5. Run the test suite and linters
6. Submit a pull request

### Pull Request Checklist

- [ ] Code follows functional programming principles
- [ ] Tests cover the new functionality or fix
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] Code passes linting checks

## Handling Complexity

When faced with complex functionality:

1. **Decompose**: Break complex functions into smaller, focused ones
2. **Compose**: Use function composition to build up complexity
3. **Data First**: Design data structures before writing functions
4. **Pure Core**: Keep core logic pure, push side effects to the edges
