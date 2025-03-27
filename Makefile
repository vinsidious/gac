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
	@NEW_VERSION=$(shell bump-my-version show) && \
	echo "## [$NEW_VERSION] - $(date +%Y-%m-%d)" >> CHANGELOG.md && \
	bump-my-version bump patch && \
	echo "New version: $NEW_VERSION"

bump-minor:
	@NEW_VERSION=$(shell bump-my-version show) && \
	echo "## [$NEW_VERSION] - $(date +%Y-%m-%d)" >> CHANGELOG.md && \
	bump-my-version bump minor && \
	echo "New version: $NEW_VERSION"

bump-major:
	@NEW_VERSION=$(shell bump-my-version show) && \
	echo "## [$NEW_VERSION] - $(date +%Y-%m-%d)" >> CHANGELOG.md && \
	bump-my-version bump major && \
	echo "New version: $NEW_VERSION"
