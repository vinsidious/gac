.PHONY: setup install install-dev dev test test-integration test-all test-cov type-check lint format clean bump bump-patch bump-minor bump-major coverage

PRETTIER_VERSION := npx prettier@3.1.0

# Create virtual environment and install dependencies
setup:
	uv venv
	uv pip install -e ".[dev]"

# Install only runtime dependencies
install:
	uv venv
	uv pip install -e .

# Update dependencies
update:
	uv pip install -U -e ".[dev]"

# Set up development environment
dev:
	@echo "Installing development dependencies..."
	uv venv
	uv pip install -e ".[dev]"
	@echo "Setting up Lefthook git hooks..."
	@if command -v lefthook >/dev/null 2>&1; then \
		lefthook install; \
		lefthook run pre-commit --all || true; \
	else \
		echo "⚠️  Lefthook not found. Install it with 'brew install lefthook' or see docs/CONTRIBUTING.md."; \
	fi
	@echo "✅ Development environment ready!"

test:
	uv run -- pytest

test-integration:
	uv run -- pytest -m integration -v

test-all:
	uv run -- pytest -m ""

test-cov:
	uv run -- python -m pytest --cov=src --cov-report=term --cov-report=html

type-check:
	uv run -- mypy src/gac

lint:
	uv run -- ruff check src/ tests/
	uv run -- ruff format --check src/ tests/
	$(PRETTIER) --check "**/*.{md,yaml,yml,json}"
	npx markdownlint-cli2 --config .markdownlint-cli2.yaml "**/*.md"

format:
	uv run -- ruff check --fix src/ tests/
	uv run -- ruff format src/ tests/
	$(PRETTIER) --write "**/*.{md,yaml,yml,json}"
	npx markdownlint-cli2 --fix --config .markdownlint-cli2.yaml "**/*.md"

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
	@# Check for uncommitted changes before starting
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Git working directory is not clean"; \
		echo "Please commit or stash your changes first"; \
		git status --short; \
		exit 1; \
	fi
	@echo "Bumping $(VERSION) version..."
	@OLD_VERSION=$$(python -c "import re; content=open('.bumpversion.toml').read(); print(re.search(r'current_version = \"([^\"]+)\"', content).group(1))") && \
	bump-my-version bump $(VERSION) --no-commit --no-tag && \
	NEW_VERSION=$$(python -c "import re; content=open('.bumpversion.toml').read(); print(re.search(r'current_version = \"([^\"]+)\"', content).group(1))") && \
	echo "Version bumped from $$OLD_VERSION to $$NEW_VERSION" && \
	python scripts/prep_changelog_for_release.py CHANGELOG.md $$NEW_VERSION && \
	git add -A && \
	git commit -m "chore: bump version to $$NEW_VERSION" && \
	git tag -a "v$$NEW_VERSION" -m "Release version $$NEW_VERSION" && \
	echo "✅ Created tag v$$NEW_VERSION" && \
	echo "📦 To publish: git push && git push --tags"

bump-patch: VERSION=patch
bump-patch: bump

bump-minor: VERSION=minor
bump-minor: bump

bump-major: VERSION=major
bump-major: bump
