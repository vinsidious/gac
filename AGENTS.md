# Repository Guidelines

This file provides guidance to AI coding agents when working with code in this repository.

## Project Structure & Module Organization

```text
gac/
├── src/gac/              # Main package
│   ├── cli.py            # CLI entrypoint
│   ├── main.py           # Commit workflow orchestration
│   ├── ai.py             # AI provider integration
│   ├── prompt.py         # Prompt building and formatting
│   ├── git.py            # Git operations
│   ├── config.py         # Configuration management
│   ├── preprocess.py     # Diff preprocessing
│   ├── security.py       # Secret detection
│   ├── errors.py         # Custom exceptions
│   ├── utils.py          # Utility functions
│   └── providers/        # AI provider implementations (~10 providers)
│       ├── openai.py
│       ├── anthropic.py
│       ├── gemini.py
│       └── ...
├── tests/                # Test suite (mirrors src/gac structure)
│   ├── conftest.py       # Shared test fixtures
│   ├── test_*.py         # Core module tests
│   └── providers/        # Provider tests (one file per provider)
│       ├── conftest.py   # BaseProviderTest framework
│       ├── test_openai.py
│       └── ...
├── docs/                 # Documentation
├── scripts/              # Automation helpers (release prep, changelog)
└── assets/               # UI screenshots and assets
```

**Key Points:**

- Python package lives in `src/gac`
- Tests mirror source structure in `tests/`
- Each provider has its own implementation file in `src/gac/providers/`
- Each provider has its own test file in `tests/providers/`
- Build artifacts (`dist/`, `htmlcov/`) are disposable - regenerate, don't commit

## Build, Test, and Development Commands

### Environment Setup

```bash
# Create development environment
make setup                          # Creates venv and installs dev dependencies
# OR manually:
uv venv && uv pip install -e ".[dev]"
```

### Daily Development

```bash
make install-dev                    # Refresh dependencies
make test                           # Run all tests (excludes integration)
make test-cov                       # Run tests with coverage (outputs to htmlcov/)
```

### Running Tests

```bash
# Default: All tests excluding integration
make test                           # Fast, for local development

# Integration tests only (requires API keys)
make test-integration               # Tests that make real API calls

# All tests including integration
make test-all                       # Complete test suite

# Targeted test runs
uv run -- pytest tests/test_cli.py                    # Single file
uv run -- pytest tests/test_cli.py::test_basic_flow   # Single test
uv run -- pytest tests/providers/test_openai.py       # Provider-specific
```

### Code Quality

```bash
make lint                           # Check with ruff, prettier, markdownlint
make format                         # Auto-fix with ruff, prettier, markdownlint
make clean                          # Remove build artifacts and caches
```

## Testing Guidelines

### Test Organization

Tests mirror the source structure. Name files as `test_<module>.py` and individual tests as `test_<behavior>`.

### Provider Test Structure

Each provider has its own test file in `tests/providers/` containing three types of tests:

**1. Unit Tests** - No external dependencies

```python
class TestOpenAIImports:
    """Test imports and basic validation."""
    def test_import_provider(self): ...
    def test_import_api_function(self): ...

class TestOpenAIAPIKeyValidation:
    """Test API key error handling."""
    def test_missing_api_key_error(self): ...
```

**2. Mocked Tests** - HTTP calls mocked, using BaseProviderTest

```python
class TestOpenAIProviderMocked(BaseProviderTest):
    """Mocked HTTP tests inheriting standard test suite."""

    @property
    def provider_name(self) -> str:
        return "openai"

    # Inherits 9 standard tests:
    # - test_successful_api_call
    # - test_empty_content_handling
    # - test_http_401_authentication_error
    # - test_http_429_rate_limit_error
    # - test_http_500_server_error
    # - test_http_503_service_unavailable
    # - test_connection_error
    # - test_timeout_error
    # - test_malformed_json_response
```

**3. Integration Tests** - Real API calls, marked with `@pytest.mark.integration`

```python
@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests with real API."""
    def test_real_api_call(self):
        """Test actual OpenAI API call with valid credentials."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        # Make real API call...
```

**Integration Test Behavior:**

- Skipped by default (don't consume API credits during development)
- Run explicitly with `make test-integration` or `make test-all`
- Skip gracefully when API keys not configured
- Use pytest marker: `@pytest.mark.integration`

### Coverage

```bash
make test-cov                       # Generates terminal + HTML report
open htmlcov/index.html             # View detailed coverage
```

Aim to maintain coverage parity. When shell-based tests are needed, add scripts under `scripts/` rather than mixing shell logic into pytest.

## Coding Style & Naming Conventions

**Python Version:** 3.10+

**Formatting:** Ruff with 120-character lines, double quotes, space indentation

**Naming Conventions:**

- `snake_case`: modules, functions, variables
- `CapWords`: classes
- `UPPER_CASE`: constants (in `constants.py`)

**Best Practices:**

- Full type annotations on all modules
- Use structured logging, not `print`
- Define CLI options through Click decorators
- Keep user-facing strings near command implementations

## Commit & Pull Request Guidelines

**Commit Format:** Conventional Commits with optional scopes

```bash
feat(ai): implement streaming support
fix(providers): handle rate limit retries
docs: update testing guidelines
```

**Commit Message Rules:**

- Summary line: imperative mood, under 72 characters
- Describe notable side effects in body
- Use `gac` to create commits (dogfooding): `gac -s <scope> -y`

**Pull Request Checklist:**

- [ ] Version bumped in `src/gac/__version__.py` (if releasable)
- [ ] `CHANGELOG.md` updated with changes
- [ ] Tests added/updated for changes
- [ ] `make lint` and `make test` passing
- [ ] Related issues linked
- [ ] Screenshots/recordings included for CLI UX changes

**Release Process:**

1. Merge PR with version bump to main
2. Create and push tag: `git tag v1.2.3 && git push origin v1.2.3`
3. GitHub Actions automatically publishes to PyPI
