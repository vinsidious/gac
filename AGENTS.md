# Repository Guidelines

## Project Structure & Module Organization

The Python package lives in `src/gac`, with CLI entrypoints in `cli.py` and orchestration logic split across modules such as `ai_providers.py`, `prompt.py`, and `git.py`. Unit and integration tests mirror that layout in `tests/`, using `test_*.py` files and shared fixtures in `conftest.py`. Reference material and process docs sit under `docs/`, UI assets and screenshots in `assets/`, and automation helpers in `scripts/` (release prep, changelog tooling). Build artifacts (`dist/`) and coverage reports (`htmlcov/`) are disposable outputs; regenerate rather than commit them.

## Build, Test, and Development Commands

Create a development environment with `make setup` (uses `uv venv` and installs `[dev]` extras). Day-to-day, `make install-dev` refreshes dependencies, `make test` runs the full pytest suite through `uv run -- pytest`, and `make test-cov` emits terminal and HTML coverage. Linting lives behind `make lint`, which chains `ruff`, `prettier`, and `markdownlint-cli2`; `make format` applies the same tools in write mode. Use targeted invocations such as `uv run -- pytest tests/test_cli.py::test_basic_flow` when iterating on a single case.

## Coding Style & Naming Conventions

Target Python 3.10+ and keep modules fully type annotated. Formatting is enforced by Ruff (`ruff format`) with 120-character lines, double quotes, and space indentation. Follow snake_case for modules, functions, and variables; reserve CapWords for classes and UPPER_CASE for constants in `constants.py`. Prefer structured logging over `print`, keep CLI options defined through Click decorators, and store user-facing strings near their command implementations for translation ease.

## Testing Guidelines

Write pytest coverage alongside features and place integration scenarios under the same `tests/` tree. Name new files `test_<module>.py` and individual tests `test_<behavior>`, mirroring existing suites.

Organize provider tests into three distinct categories for better maintainability:

- **Unit tests** (`test_providers_unit.py`): Pure unit tests with no external dependencies
- **Mocked tests** (`test_providers_mocked.py`): Tests with mocked HTTP calls that verify internal logic
- **Integration tests** (`test_providers_integration.py`): Tests that make real API calls (marked with pytest markers)

Aim to maintain coverage parity by running `make test-cov`; HTML output lands in `htmlcov/index.html` for inspection. When shell-based repro steps are needed, add helper scripts under `scripts/` instead of mixing shell logic into pytest.

## Commit & Pull Request Guidelines

History follows Conventional Commits with optional scopes (for example, `feat(ai): implement streaming support`). Keep summary lines imperative, under 72 characters, and describe notable side effects in the body. We dogfood `gac`: craft commit messages with the local `gac` CLI, or fall back to `uvx gac` if the local fails. Release-worthy work must bump `src/gac/__version__.py` and update `CHANGELOG.md`. Pull requests should link related issues, explain testing performed, and include screenshots or recordings when CLI UX changes. Run `make lint` and `make test` before requesting review to avoid CI churn.
