.PHONY: setup install install-dev test lint format clean bump-patch bump-minor bump-major bump-alpha bump-beta bump-rc

# Create virtual environment and install dependencies
setup:
	uv venv
	uv pip install -e ".[dev]"

# Install only runtime dependencies
install:
	uv pip install -e .

# Install with development dependencies
install-dev:
	uv pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run linting
lint:
	black --check .
	isort --check .
	flake8 .

# Format code
format:
	black .
	isort .

# Update dependencies
update:
	uv pip install -U -e ".[dev]"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Version bumping
bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major

bump-alpha:
	bump2version release --new-version=a

bump-beta:
	bump2version release --new-version=b

bump-rc:
	bump2version release --new-version=rc
