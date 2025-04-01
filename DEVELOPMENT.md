# GAC Development Guide

## Project Overview

Git Auto Commit (GAC) is a CLI tool designed with functional programming principles to generate intelligent commit messages using AI.

## Development Philosophy

### Core Principles

1. **Functional Programming**

   - Emphasize pure functions
   - Minimize side effects
   - Prefer immutability
   - Compose complex behaviors from simple functions

2. **Modularity**

   - Clear separation of concerns
   - Easy to test and extend
   - Minimal dependencies between modules

3. **Testability**
   - Comprehensive test coverage
   - Behavior-driven testing
   - Minimal mocking

## Getting Started

### Prerequisites

- Python 3.10+
- uv (recommended for dependency management)
- Git
- Virtual environment support

### Setup

```bash
# Clone the repository
git clone https://github.com/cellwebb/gac.git
cd gac

# Create virtual environment and install dependencies
make setup  # Uses uv to manage dependencies

# Activate virtual environment
source .venv/bin/activate
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage

# Run linting
make lint

# Format code
make format
```

### Code Style

- Use Black for formatting
- Use isort for import sorting
- Follow PEP 8 guidelines
- Write type hints
- Use docstrings for all public functions

### Writing Tests

- Use pytest
- Focus on testing behavior, not implementation
- Use fixtures for setup and teardown
- Aim for high test coverage
- Use property-based testing where possible

### Commit Message Guidelines

1. Use conventional commits format
2. Describe the change, not the implementation
3. Be concise but informative

## Architecture

### Module Structure

```
src/gac/
├── ai.py            # AI provider integration
├── cli.py           # Command-line interface
├── config.py        # Configuration management
├── errors.py        # Error handling
├── format.py        # Code formatting
├── git.py           # Git operations
├── prompt.py        # Prompt generation
└── utils.py         # Utility functions
```

### Key Design Principles

- **Pure Functions**: Functions should have no side effects
- **Immutable Data**: Prefer creating new objects over modifying existing ones
- **Explicit Dependencies**: Pass all dependencies as arguments
- **Error Handling**: Use result types and explicit error propagation

## Contributing

### Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Submit a pull request

### Pull Request Checklist

- [ ] Code follows functional programming principles
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Code passes linting checks

## Performance Considerations

- Use `functools.lru_cache` for memoization
- Profile code performance
- Minimize unnecessary computations
- Use lazy evaluation when possible

## Advanced Development

### Debugging

```bash
# Enable debug logging
GAC_LOG_LEVEL=DEBUG gac

# Show AI prompt details
gac --show-prompt
```

### Performance Profiling

```bash
# Profile the application
python -m cProfile -o profile.out gac
```

## Release Process

```bash
# Bump version
make bump-patch  # or make bump-minor, make bump-major

# Create release
make release
```

## Recommended Tools

- Black: Code formatting
- isort: Import sorting
- pytest: Testing
- mypy: Static type checking
- coverage: Test coverage
- uv: Dependency management

## Community and Support

- Open GitHub Issues for bugs and feature requests
- Join our discussion forums
- Contribute by submitting pull requests

## License

GAC is released under the MIT License. Contributions are welcome!
