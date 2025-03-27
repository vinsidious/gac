.PHONY: setup install install-dev test lint format clean bump bump-patch bump-minor bump-major bump-alpha bump-beta bump-rc

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
bump:
	@git diff --exit-code || (echo "Git working directory is not clean" && exit 1)
	@NEW_VERSION=$$(bump-my-version show | grep "current_version" | cut -d "'" -f4) && \
	python scripts/prep_changelog_for_release.py CHANGELOG.md $$NEW_VERSION && \
	git add CHANGELOG.md && \
	git commit -m "Update CHANGELOG.md for version $$NEW_VERSION" && \
	bump-my-version bump $(VERSION) && \
	echo "New version: $$NEW_VERSION"

bump-patch: VERSION=patch
bump-patch: bump --commit --tag --push

bump-minor: VERSION=minor
bump-minor: bump --commit --tag --push

bump-major: VERSION=major
bump-major: bump --commit --tag --push
