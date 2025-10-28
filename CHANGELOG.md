<!-- markdownlint-disable MD013 MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.12.1] - 2025-10-28

### Fixed

- Correct Gemini provider payload to use `systemInstruction` and Gemini-supported roles, resolving API role validation errors
- Skip empty text parts in Gemini responses so reasoning models return commit messages reliably

## [1.4.1] - 2025-10-04

### Note

- This release is purely to correct a versioning issue with PyPI. The actual code changes are in 1.4.0.

## [1.4.0] - 2025-10-04

### Added

- Add dedicated `zai-coding` AI provider for direct access to Z.AI coding API

### Changed

- Refactor Z.AI provider implementation to use shared API call logic
- Update CLI setup flow to support explicit "Z.AI Coding" provider selection
- Improve error messaging and test coverage for Z.AI providers
- Simplify `call_zai_api` function to only handle regular Z.AI endpoint

### Removed

- Remove environment variable `GAC_ZAI_USE_CODING_PLAN` dependency for API endpoint selection

## [1.3.1] - 2025-10-03

### Fixed

- Support for zai AI provider in the generation utilities

## [1.3.0] - 2025-10-03

### Added

- Support for Z.AI coding API endpoint with new environment variable configuration
- Built-in security scanner to detect secrets and API keys in staged changes
- CLI option to skip security scanning (--skip-secret-scan)
- Enhanced secret pattern matching including access_key and secret_key detection

### Changed

- Refactor core console initialization to global level and improve option display formatting
- Update OpenRouter provider with better error handling for rate limits and service unavailability
- Modify security scanning to use click.prompt for improved CLI interaction
- Improve diff section parsing with proper git diff structure validation

### Fixed

- Security warning styling and user choice handling for better readability
- Line number tracking accuracy in diff parsing by handling context lines properly

### Security

- Enhance staged file security scanning with secret detection
- Expand false positive filtering to include example environment files and documentation
- Add configurable blocking or warning options for secret detection
- Implement interactive remediation choices when secrets are detected

## [1.2.6] - 2025-10-01

### Changed

- Refactor provider test suite into three distinct categories: unit, mocked HTTP, and integration tests
- Update Makefile with new targets for running specific provider test categories
- Revise AGENTS.md documentation to reflect new provider testing organization

### Removed

- Obsolete test files `test_ai_providers_simple.py` and `test_ai_providers_unit.py` after test reorganization

## [1.2.5] - 2025-10-01

### Added

- Add Z.AI as a new AI provider for commit message generation
- Support ZAI_API_KEY environment variable in .gac.env.example
- Include Z.AI in the list of supported AI providers in README.md
- Implement call_zai_api function for Z.AI model integration

## [1.2.4] - 2025-09-29

### Added

- Comprehensive AI provider integration tests for OpenAI, Anthropic, OpenRouter, Groq, Cerebras, and Ollama
- New Makefile targets: `test-providers` and `test-all` for running provider integration tests
- Pytest markers and configuration to manage provider integration test execution

### Changed

- Default test execution now excludes provider integration tests to avoid API usage during development
- Contribution documentation updated with instructions for running provider integration tests
- Test suite configuration to skip provider tests unless explicitly requested

## [1.2.3] - 2025-09-28

### Fixed

- Correct OpenAI API parameter name from `max_tokens` to `max_completion_tokens` to resolve token limit issues

## [1.2.2] - 2025-09-28

### Removed

- Remove optional OpenRouter site URL and name headers (BREAKING: drops support for OPENROUTER_SITE_URL and OPENROUTER_SITE_NAME environment variables)
- Remove commented configuration examples for OpenRouter site-specific headers from README

### Changed

- Refactor OpenRouter API call to simplify header handling by removing conditional logic for optional headers
- Update test case to reflect simplified OpenRouter API call without optional headers

## [1.2.1] - 2025-09-28

### Changed

- Refactor AI generation logic to improve reliability and error handling
- Enhance token counting with better fallback mechanisms and remove provider-specific implementations
- Improve error classification and propagation in AI generation retries
- Update test suite to align with unified AI generation API approach

### Removed

- Deprecated Anthropic token counting implementation and associated API calls
- Legacy AI provider test functions in favor of new call\_\*\_api methods

### Fixed

- Resolve issue where AIError exceptions were not properly re-raised during commit message generation
- Address empty or None content responses from AI models with clearer error messaging
- Correct httpx mocking approach in provider tests to patch direct post calls

## [1.2.0] - 2025-09-28

### Changed

- Refactor AI provider architecture to consolidate calls and centralize retry logic
- Update all AI provider modules to expose unified `call_*_api` functions
- Replace individual provider retry and spinner implementations with centralized `generate_with_retries` utility
- Modify `ai.generate_commit_message` to support both tuple and string prompt formats
- Simplify imports across provider modules and `ai.py` to use new call functions interface
- Adjust tests to import `AIError` directly from errors module

### Removed

- Legacy retry and spinner code duplicated across individual AI provider implementations
- Direct generate function imports from provider modules in main `__init__.py` file

## [1.1.0] - 2025-09-27

### Added

- Support for OpenRouter provider in commit message generation
- New AI error handling class (AIError) in errors module

### Changed

- Refactor AI providers into modular architecture with individual provider modules
- Centralize prettier command version in Makefile for consistent usage
- Update README documentation to include OpenRouter configuration details

### Removed

- Monolithic ai_providers.py file in favor of provider-specific modules

## [1.0.1] - 2025-09-26

### Added

- Implement Anthropic token counting via HTTP API with fallback to heuristic estimation
- Add new helper function `anthropic_count_tokens` for API-based token counting
- Include comprehensive tests for Anthropic token counting scenarios
- Use httpx for HTTP requests instead of direct anthropic SDK usage

### Changed

- Update `count_tokens` to delegate Anthropic counting to helper function
- Add proper error handling and logging for Anthropic API failures

## [1.0.0] - 2025-09-26

### Added

- Implement direct API calls to AI providers (OpenAI, Anthropic, Groq, Cerebras, Ollama) using httpx
- Add Anthropic SDK dependency for token counting functionality
- Introduce repository guidelines document (AGENTS.md) covering project structure, development workflow, coding style, testing, and commit conventions

### Changed

- Replace aisuite library abstraction with direct HTTP API calls for improved reliability and reduced dependencies
- Refactor test structure to validate API key handling per AI provider and improve validation coverage
- Update markdownlint configuration to disable line length enforcement
- Modify generate_commit_message tests to use httpx client mocks
- Adjust parameter passing in AI tests to match new positional arguments
- Consolidate error classification tests into ai_providers_unit module

### Removed

- Remove aisuite dependency and all associated abstraction layer code
- Remove redundant mock setup and streamline test dependencies in AI provider tests
- Remove unused helper function tests from ai_providers_simple module
- Remove monolithic provider file structure in favor of direct API implementations

## [0.19.1] - 2025-09-22

### Changed

- Upgrade all AI provider SDKs to latest stable versions for improved functionality and performance
- Pin cerebras_cloud_sdk to v1.49.0 for enhanced stability
- Update pydantic to v2.11.9 for better data validation capabilities
- Refresh core dependencies including click, rich, and python-dotenv for improved CLI experience and formatting

## [0.19.0] - 2025-05-15

### Changed

- **Simplified Scope Flag Implementation**: Refactored the `--scope`/`-s` flag to be a simple boolean flag that triggers scope inference rather than accepting scope values
  - Modified CLI to make `-s` flag a simple boolean switch instead of accepting values
  - Updated prompt system to handle boolean `infer_scope` parameter instead of string values
  - Simplified configuration logic while preserving `always_include_scope` functionality
  - Removed deprecated scope value passing functionality
  - All scope-related tests updated to reflect new boolean-based implementation

## [0.18.1] - 2025-09-21

### Added

- **Code Formatting Consistency**: Added `.prettierrc` configuration file for consistent code formatting
  - Defines explicit prettier configuration to ensure consistent formatting across environments
  - Sets print width to 120 characters to match markdownlint configuration
  - Configures standard formatting options for JSON, YAML, and markdown files
- **Dependency Lock File**: Added `uv.lock` file for reproducible builds
  - Ensures all team members and CI/CD pipelines use exact same dependency versions
  - Provides deterministic dependency resolution across different environments
  - Improves build reliability and reduces "works on my machine" issues

### Changed

- **Build System Modernization**: Replaced individual linting tools with ruff for streamlined development
  - Replaced black, isort, and flake8 with ruff in Makefile lint and format commands
  - Removed individual tool dependencies from pyproject.toml
  - Uses `uv run` prefix for consistent tool execution within virtual environment
  - Significantly simplifies development tooling while maintaining code quality
- **Pre-commit Hooks**: Migrated to ruff for faster linting and formatting
  - Replaced black, isort, and flake8 with ruff in pre-commit configuration
  - Uses `uvx ruff` for even faster execution without separate virtual environments
  - Matches CI/CD pipeline tooling for consistency
  - Significantly reduces pre-commit hook execution time

## [0.18.0] - 2025-09-15

### Added

- **Dependency Lock File**: Added `uv.lock` file for reproducible builds
  - Ensures all team members and CI/CD pipelines use exact same dependency versions
  - Provides deterministic dependency resolution across different environments
  - Improves build reliability and reduces "works on my machine" issues

### Fixed

- **Token Counting for Anthropic Models**: Improved accuracy and reliability

  - Updated to use Anthropic's new beta token counting API for precise token counts
  - Added proper model name extraction from provider-prefixed model strings
  - Implemented fallback estimation when API is unavailable
  - Fixed deprecated `Client().count_tokens()` usage

- **Comprehensive Test Coverage**: Expanded test suite for AI module
  - Added extensive tests for `generate_commit_message()` function
  - Added tests for retry logic with exponential backoff
  - Added tests for error classification (authentication, rate limit, timeout, etc.)
  - Added tests for both string and tuple prompt formats
  - Added tests for spinner integration in non-quiet mode
  - Improved test coverage for edge cases and error scenarios

## [0.17.7] - 2025-09-15

### Added

- Improve Anthropic token counting with dynamic model detection and beta API integration

## [0.17.6] - 2025-09-15

### Fixed

- Update Anthropic token counting method to use the correct client initialization and provide rough estimates for newer models

## [0.17.5] - 2025-09-14

### Added

- Support for dual-prompt system architecture with separate system and user prompt components
- Comprehensive AI module tests including error handling and various content type validation
- Enhanced CI/CD workflows with matrix strategy for multi-version Python testing

### Changed

- Refactor AI generation to handle new prompt tuple format while maintaining backward compatibility
- Modernize CI/CD workflows by splitting quality job into lint/test jobs and using uv for dependency management
- Update bumpversion configuration from cfg to toml format
- Improve version bump safety checks with robust git status validation
- Replace grep/cut version extraction with python regex for reliability
- Modify token counting to account for both system and user prompts with fallback character-based estimation

### Removed

- Monolithic prompt generation file structure
- Redundant test uploads and coverage reports for Python versions other than 3.11
- Legacy pip-based dependency installation in CI/CD workflows
- .bumpversion.cfg configuration file

## [0.17.4] - 2025-09-14

### Changed

- **Improved AI Prompt Architecture**: Separated prompt generation into system and user components for better AI model interaction

  - Modified `build_prompt()` to return a tuple of `(system_prompt, user_prompt)` instead of a single concatenated string
  - System prompt now contains role definition, instructions, conventions, and examples
  - User prompt contains only the actual git data (status, diff, diff_stat, and optional hints)
  - Updated `generate_commit_message()` to support both tuple format (new) and string format (backward compatible)
  - AI providers now receive properly structured messages with separate system and user roles
  - Improved token counting to accurately reflect both system and user prompt usage
  - Maintains full backward compatibility with existing code using string prompts

- **Enhanced CI/CD Workflows**: Modernized GitHub Actions workflows with uv/uvx for better performance

  - Split single quality job into separate lint and test jobs for parallel execution
  - Added test matrix to run tests across Python 3.10, 3.11, 3.12, and 3.13
  - Replaced pip with uv for faster dependency resolution and caching
  - Use uvx to run tools in isolated environments without system pollution
  - Optimized coverage reporting to upload only once per workflow run

- **Improved Version Bumping**: Migrated from deprecated .cfg to modern .toml configuration
  - Created `.bumpversion.toml` to replace deprecated `.bumpversion.cfg`
  - Enhanced Makefile bump commands with better error handling and user feedback
  - Added robust git status checks before version bumping
  - Improved version extraction using Python regex for reliability
  - Automated changelog updates during version bumping process

## [v0.17.3] - 2025-09-14

### Changed

- **Tag-Based Release Workflow**: Switched to tag-triggered releases for better control
  - CI/CD now publishes to PyPI only when version tags are pushed (e.g., `v0.17.3`)
  - Removed complex auto-version-bumping logic
  - Allows batching multiple PRs before releasing
  - Prevents accidental releases and "file already exists" errors
  - Verifies tag version matches code version before publishing
  - Updated documentation to explain tag-based release process

## [v0.17.2] - 2025-09-14

### Fixed

- **Push Failure Reporting**: Fixed issue where git push failures were incorrectly reported as successful when using the `-p` flag
  - Updated `push_changes()` function to use `run_subprocess()` with `raise_on_error=True` for accurate failure detection
  - Replaced generic error handling with specific `subprocess.CalledProcessError` handling to capture git push stderr output
  - Modified main function to properly exit with error code 1 when push operations fail
  - Improved error messages to include network connection troubleshooting hints
  - Updated test suite to match the new implementation and ensure push failures are properly detected

## [v0.17.0] - 2025-09-14

### Added

- **Always Include Scope Configuration**: Added new `GAC_ALWAYS_INCLUDE_SCOPE` environment variable to enable automatic scope inference

  - When enabled, gac will automatically infer commit scope even when not explicitly provided via `--scope` flag
  - Added configuration option to control whether commits require explicit scope or can infer it automatically
  - Updated CLI to respect the always_include_scope setting when no explicit scope is provided
  - Added comprehensive tests covering config loading and CLI behavior with scope inference
  - Included example env configuration for the new always_include_scope option

- **Enhanced Reroll Functionality with User Feedback**: Improved the commit message reroll capability to accept user-provided feedback
  - Introduced support for providing feedback during commit message reroll via "r \<feedback\>" input format
  - Modified confirmation prompt to inform users about the new reroll with feedback option
  - Combined initial hint with reroll feedback to create conversational context for regeneration
  - Preserved original prompt when no reroll feedback is provided for backward compatibility
  - Improved validation logic to handle case-insensitive user responses
  - Added blank line for improved console output readability during reroll process

### Improved

- **Documentation Enhancement**: Updated documentation to reflect new interactive reroll capabilities
  - Enhanced README.md to document the new interactive reroll capability that accepts feedback
  - Modified USAGE.md to detail how users can provide specific regeneration hints
  - Added documentation for advanced configuration options including scope and AI settings
  - Clarified the difference between simple reroll and feedback-assisted message regeneration
  - Included examples of how to use the new reroll with feedback functionality
  - Updated warning message capitalization for better visibility

## [v0.16.3] - 2025-09-14

### Fixed

- **Documentation Commit Type Detection**: Fixed issue where documentation-only changes were incorrectly labeled as `feat` or `refactor` instead of `docs` (#33)
  - Updated prompt template to properly determine commit type based on PRIMARY purpose of changes
  - Refined logic to use `docs:` ONLY when ALL changes are documentation files
  - For mixed changes (code + docs), now correctly prioritizes the code change type
  - Reduced documentation file importance scores (`.md`, `.rst`) from 4.0/3.8 to 2.5 to ensure proper prioritization
  - Added comprehensive test suite for documentation-only change detection
  - Ensures README and other documentation updates are correctly classified regardless of content significance

### Improved

- **Commit Message Generation Quality**: Enhanced prompt template with better guidance for AI models
  - Added `<focus>` section to prioritize core purpose and impact in commit messages
  - Added `<mixed_changes>` section with clear rules for handling multi-area changes
  - Enhanced scope inference with better guidance for component and module naming
  - Simplified example structure to two sections: no-scope and with-scope examples
  - Improved template consistency by aligning examples pattern with conventions sections
  - Examples now always match the expected output format for each scope mode
- **Pre-commit Hook Error Reporting**: Enhanced error messages when pre-commit hooks fail
  - Now displays detailed output showing which specific hooks failed and why
  - Captures and displays both stdout and stderr from pre-commit
  - Replaces generic "exit code 1" message with actionable failure information
- **Git Module Test Coverage**: Added comprehensive tests for all git module functions
  - Added tests for `get_staged_files` with various filtering options
  - Added tests for `get_diff` covering staged, unstaged and commit comparison scenarios
  - Added tests for `push_changes` covering all error and success cases

## [v0.16.2] - 2025-09-14

### Fixed

- **CI Version Management**: Improved version bumping in publish workflow
  - Automatically syncs `__version__.py` and `.bumpversion.cfg` to use the higher version if they differ
  - Prevents double version bumping when merging PRs that already contain version changes
  - Checks both version files for modifications before auto-bumping
  - Works correctly with any git merge strategy (squash, merge commit, rebase)
  - Ensures version consistency across both configuration files

## [0.16.1] - 2025-09-14

### Changed

- Bump version to 0.16.1 for minor release updates

## [v0.16.0] - 2025-09-14

### Added

- **Cerebras AI Provider Support**: Added comprehensive support for Cerebras AI models

  - Added `cerebras_cloud_sdk` dependency to pyproject.toml
  - Updated init CLI to include Cerebras with qwen-3-coder-480b as default model
  - Added CEREBRAS_API_KEY to example configuration file
  - Updated README to list Cerebras as a supported provider

- **Test Coverage**: Added comprehensive tests for new features
  - Added tests for project-level `.gac.env` file loading with proper isolation
  - Added tests for `.env` file fallback behavior when `.gac.env` doesn't exist
  - Added tests for configuration precedence validation
  - Added tests for Anthropic token counting implementation
  - Improved test isolation using temporary directories and Path.home mocking

### Changed

- **Configuration Loading**: Improved configuration file loading precedence
  - Now properly supports project-level `.gac.env` files (not just `.env`)
  - Loading order (each level overrides the previous):
    1. `$HOME/.gac.env` (user-level config)
    2. `./.gac.env` OR `./.env` (project-level config, `.gac.env` takes precedence if both exist)
    3. Environment variables (highest priority)
  - Project config files override user config when present

### Fixed

- **Anthropic Token Counting**: Fixed AttributeError with Anthropic API
  - Changed from `client.messages.count_tokens()` to `client.count_tokens(text)`
  - Simplified token counting implementation for Anthropic models
- **Error Handling**: Fixed console initialization in AIError exception handler
  - Console is now properly initialized when catching AIError exceptions
  - Prevents "console not defined" errors during error handling

## [0.15.4] - 2025-09-14

### Added

- Quick try instructions using uvx for testing gac without permanent installation

### Changed

- Simplify installation command to use 'pipx install gac' instead of GitHub repository URL
- Update README title to "Git Auto Commit (gac)" for improved readability
- Reorder README badges to prioritize build status and code coverage metrics
- Modify pyproject.toml build configuration to properly include source files

## [0.15.1] - 2025-09-14

### Changed

- Bump version to 0.15.1 for minor release update

## [v0.15.0] - 2025-06-08

### Added

- **PyPI Release**: Published package to PyPI for easy installation via pip
- **Quick Try with uvx**: Added support for trying gac without installation using uvx
- **Modern CI/CD Pipeline**: Implemented auto-publishing with ruff and modern tooling

### Changed

- **Build System**: Switched from VCS versioning to static version management
- **Dependencies**: Updated and modernized dependency management with uv dependency groups
- **Documentation**: Improved README with better installation instructions and badges
- **Repository Structure**: Updated URLs and references for PyPI compatibility

### Removed

- **VSCode Configuration**: Removed VSCode configuration files from repository
- **CLA Requirement**: Removed CLA requirement from project

## [v0.14.7] - 2025-06-06

### Added

- **Diff Statistics Enhancement**: Added support for displaying git diff statistics in commit message prompt to provide more context for AI.

### Changed

- **Prompt Building Refactor**: Improved separation of concerns in prompt building:
  - Moved diff preprocessing logic from `build_prompt()` to `main.py`
  - Removed unused `model` parameter from `build_prompt()` function
  - Simplified function signature by removing template path parameter

### Technical

- Enhanced single responsibility principle in code organization
- Improved maintainability by removing parameter passing for unused values
- Updated tests to reflect the new function signatures

## [v0.14.6] - 2025-06-06

### Added

- **Pre-commit Hook Integration**: Added comprehensive pre-commit hook execution before commits.
  - Automatically runs pre-commit hooks when `.pre-commit-config.yaml` exists
  - Validates hooks pass before proceeding with expensive AI operations
  - Graceful fallback when pre-commit is not installed
- **Enhanced Error Handling**: Improved subprocess error handling with consistent CalledProcessError conversion.

### Improved

- **User Experience**: Better error messages when pre-commit hooks fail with guidance to use `--no-verify`.
- **Documentation Updates**:
  - Enhanced `--no-verify` flag documentation in USAGE.md with clearer formatting and use cases
  - Added Pre-commit Hook Issues section to TROUBLESHOOTING.md with common solutions
  - Improved troubleshooting guide structure and navigation
- **Code Organization**: Cleaned up imports in `__init__.py` by removing unused constants imports.

### Fixed

- **Test Reliability**: Updated all scope and token usage tests to properly mock pre-commit hooks.
- **Subprocess Error Handling**: Consistent error type conversion in `run_subprocess` utility function.

### Technical

- Added `run_pre_commit_hooks()` function in `git.py` for centralized hook management.
- Enhanced test coverage for pre-commit integration scenarios.
- Improved error propagation consistency across subprocess calls.

## [v0.14.5] - 2025-06-06

### Fixed

- **Whitespace Handling**: Collapsed blank lines containing spaces or tabs in
  commit messages and prompt templates.

## [v0.14.4] - 2025-06-02

### Added

- **Pre-commit Integration**: Added comprehensive pre-commit hooks configuration for code quality enforcement.
- **--no-verify Flag**: Added new CLI flag to skip pre-commit hooks when needed.
- **Upstream Check Hook**: Added custom pre-commit hook to check if local branch is up-to-date with remote before committing.

### Improved

- **Code Quality Tools**: Integrated black, isort, flake8, markdownlint-cli2, and prettier via pre-commit.
- **Flake8 Configuration**: Configured flake8 to ignore line length checks (E501) since black handles formatting.
- **Documentation**: Added pre-commit setup instructions to CONTRIBUTING.md.
- **USAGE Documentation**: Added advanced section documenting the --no-verify flag usage.

### Fixed

- **Duplicate Code**: Removed duplicate `get_staged_files()` call in dry-run mode.

### Technical

- Updated pre-commit hook versions: black (25.1.0), isort (6.0.1), flake8 (7.2.0), markdownlint-cli2 (v0.18.1).
- Added flake8-bugbear as additional dependency for enhanced linting.
- Created `.githooks/check-upstream` script for checking remote synchronization.

## [v0.14.3] - 2025-05-30

### Added

- **Reroll Capability**: Added ability to regenerate commit messages by typing `r` or `reroll` at the confirmation prompt.
- **Enhanced Scope Handling**: Completely revamped the scope handling system with dedicated templates for different scenarios.

### Improved

- **Message Cleaning**: Added detection and fixing of double type prefix issues in generated commit messages.
- **Confirmation Flow**: Redesigned the confirmation prompt to clearly accept `y/n/r` inputs with improved user guidance.
- **Temperature Setting**: Increased default temperature from 0.7 to 1.0 for more creative commit message generation.

### Fixed

- Fixed issue with scope handling in commit message generation.
- Improved handling of commit message formatting and validation.

### Documentation

- Updated README and USAGE documentation to reflect the new reroll capability.
- Expanded USAGE.md with clearer explanation of confirmation prompt options.

## [v0.14.2] - 2025-05-29

### Added

- Token counting functionality for tracking token usage in commit message generation.
- Detailed token usage reporting in the console output.

### Improved

- Enhanced analytics for token distribution in commit message generation.
- Updated documentation with examples of token count reporting.

### Technical

- Integrated token counting logic into the core processing modules.
- Added token count validation to ensure accurate reporting.
- Updated test suite to include token counting verification.

### Documentation

- Added token counting details to the relevant documentation sections.
- Included examples of token usage reports in the user guide.

## [v0.14.1] - 2025-05-27

### Changed

- Updated provider list in `gac init`: added Ollama with `gemma3` as the default model.
- Simplified installation instructions and updated command examples in `README.md`.
- Corrected previous changelog entry for v0.14.0 by removing an inaccurate statement about an OpenRouter model update.

### Refactor

- Removed `extract_repository_context` function and its usage in `build_prompt` from `src/gac/prompt.py` to simplify prompt generation and reduce token usage.

### Fixed

- Improved `clean_commit_message` function in `src/gac/prompt.py` for better formatting of commit messages.

## [v0.14.0] - 2025-05-27

### Added

- Implemented `--scope` / `-s` command-line flag to allow specifying a scope for commit messages.
  - Supports providing a specific scope.
  - Supports requesting AI to determine the scope.
  - Supports omitting scope.
- Enhanced `gac diff` command:
  - Displays diffs for staged or unstaged changes.
  - Allows comparison between specific commits.
- Added extensive tests for new scope and diff functionalities, and increased overall test coverage.

### Changed

- Simplified the `gac init` command by removing the backup model setup flow.
- Simplified prompt instructions by removing explicit scope examples.
- Revised `README.md` and `INSTALLATION.md` to reflect simplifications and removed features.
- Updated tests to accommodate removed features and other code changes.

### Removed

- Backup model functionality: removed `GAC_BACKUP_MODEL`, associated fallback logic (`generate_with_fallback`), and
  related configurations.
- File formatting feature: deleted `src/gac/format.py`, related configurations, and calls from `gac.main`.
- `gac preview` CLI command and its implementation (`src/gac/preview_cli.py`).
- CLA assistant GitHub workflow (`.github/workflows/cla.yml`).

## [v0.13.1] - 2025-05-26

### Fixed

- Fixed filtered file handling to show summaries instead of hiding them completely
  - Binary files now display as `[Binary file change]`
  - Lockfiles and generated files show as `[Lockfile/generated file change]`
  - Minified files show as `[Minified file change]`
  - Affects both `gac diff` command output and the context sent to LLMs for commit message generation by `gac`
  - This ensures users and LLMs are aware of all file changes while keeping output clean

## [v0.13.0] - 2025-05-25

### Added

- New `gac preview` command to generate commit messages for diffs without committing
  - Preview changes against HEAD or between specific commits
  - Supports all message generation options (one-liner, hint, model selection)
  - Displays formatted commit message preview
- Integration test script for preview functionality (`scripts/test_gac_preview.sh`)
- Improved installation instructions with step-by-step commands in README.md
- Unit tests for the preview command in `tests/test_cli.py`

### Changed

- Reorganized documentation files into `docs/` directory for better organization
  - Moved `INSTALLATION.md`, `USAGE.md`, `CONTRIBUTING.md`, and `TROUBLESHOOTING.md`
  - Updated all cross-references in README.md and other files
- Improved prompt handling in `prompt.py`:
  - Renamed `add_repository_context` to `extract_repository_context` for clarity
  - Better handling of hints and empty repository context
  - Fixed placeholder in prompt template (`<hint_text>` instead of `<context>`)
- Removed codecov.yml in favor of GitHub default settings

### Fixed

- Corrected links to documentation files in README.md
- Enhanced error handling in preview functionality for invalid git refs

## [0.12.0] - 2025-05-07

### Added

- Add `preview` CLI command for generating commit message previews based on git diffs
- Implement diff comparison logic for commit message generation
- Create `preview_cli.py` module to handle preview command functionality
- Add `test_gac_preview.sh` integration test script for GAC preview feature

### Changed

- Refactor documentation files into dedicated `docs/` directory for better organization
- Update README.md links to point to new documentation file locations
- Improve installation instructions with direct pipx install commands and verification steps
- Enhance CLI test coverage to include preview command error handling scenarios

### Removed

- Remove codecov configuration file to declutter repository
- Eliminate redundant documentation files from root directory after reorganization

## [v0.11.0] - 2025-04-18

### Added

- Interactive `gac init` command for guided provider/model/API key configuration.
- Improved documentation for installation, configuration, and troubleshooting (`INSTALLATION.md`, `TROUBLESHOOTING.md`,
  `README.md`)
- Registration links for Groq, Anthropic, OpenAI, and Mistral in docs
- Clearer explanation of environment variable usage and config file precedence

### Changed

- Provider API key environment variables now use standard names (`GROQ_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- `gac init` and documentation updated to reserve `GAC_` prefix for internal config (e.g., `GAC_MODEL`)
- Roadmap simplified to focus on next updates and historical milestones
- Troubleshooting guide now distinguishes project-level and user-level `.gac.env` issues, with OS-specific guidance

### Fixed

- Test for `gac init` updated to expect new environment variable naming
- Minor formatting and consistency improvements in documentation and CLI output

## [v0.10.0] - 2025-04-18

### Added

- Dedicated `config_cli.py` for managing user-level configuration via CLI subcommands
- `gac config` subcommands: `show`, `set`, `get`, `unset` for easy config management in `$HOME/.gac.env`
- Unified CLI: now supports both top-level flags and subcommands (no more `gac run` wrapper)
- `scripts/test_gac_sandbox.sh` to test the GAC CLI in a sandboxed environment
- `tests/test_config_cli.py` to test the config CLI using Click's testing utilities

### Changed

- Refactored CLI entry point and wiring for greater extensibility
- Simplified configuration precedence: user-level `$HOME/.gac.env` and project-level `.env` (with env vars always taking
  precedence)
- Updated documentation to reflect new configuration workflow and CLI usage (README.md, USAGE.md, ROADMAP.md)

### Removed

- Old project-level `.gac.env` and package-level `_config.env` from config precedence
- Obsolete test code for CLI (see `tests/test_cli.py`)
- Outdated or redundant configuration documentation in roadmap and docs

### Fixed

- Minor formatting and lint issues in test and preprocess modules

## [v0.9.3] - 2025-04-17

### Changed

- Refined CI workflow to ignore additional files and directories, reducing unnecessary runs and noise
- Improved consistency in documentation and configuration management

### Documentation

- Updated roadmap to reflect completed and in-progress tasks
- Preparation for advanced configuration system implementation

## [v0.9.2] - 2025-04-17

### Added

- `test_cli.py` to test the command line interface
- `test_config.py` to test configuration loading
- Additional test cases in `test_preprocess.py`
- Additional test cases in `test_utils.py`

### Changed

- Documentation for Windows compatibility (see [docs/WINDOWS_COMPATIBILITY_PLAN.md](docs/WINDOWS_COMPATIBILITY_PLAN.md))
- Updated `README.md`, `INSTALLATION.md`, `USAGE.md`, and `ROADMAP.md` to reflect Python 3.10+ and Windows support
- Modified `cli.py` to print version information instead of logging it
- Updated `conftest.py` to silence noisy loggers during testing
- Improved code coverage by adding new test files and cases

## [v0.9.1] - 2025-04-17

### Changed

- Relocated CLI entry point from `src/gac/main.py` to `src/gac/cli.py` to improve modularity and separation of concerns
- Updated `pyproject.toml` to point at the new CLI entry location
- Simplified `main.py` to focus solely on business logic by removing CLI wiring
- Improved overall code organization and maintainability by isolating CLI-specific code

## [v0.9.0] - 2025-04-17

### Added

- Introduced configuration management via a dedicated config.py module for improved organization and reusability.
- Implemented hierarchical configuration loading with support for environment files and variables.
- Enhanced logging setup with customizable log levels, quiet mode, and suppression of noisy loggers.

### Changed

- Updated main entry point to leverage the new configuration and logging features.

### Refactored

- Removed unnecessary pytest import from test_git.py.

## [v0.8.0] - 2025-04-14

### Added

- Git utility functions for repository root, current branch, and commit hash
- Code formatting functions with Black integration
- New test cases for git utilities and code formatting
- Coverage configuration to exclude main.py
- CONTRIBUTING.md with guidelines for project contributions
- LICENSE file with MIT license
- Verbose logging option to CLI

### Changed

- Improved test parameterization in test_format.py
- Updated import statements for better organization
- Enhanced code formatting validation logic
- Improved push change handling with enhanced logging and user feedback
- Updated installation documentation for clearer configuration instructions
- Updated README with project badges and contributing information
- Refined linting commands to use check mode for black, isort, and prettier
- Updated VSCode settings to exclude more files from file explorer

### Documentation

- Enhanced dry run logging for push changes
- Improved installation and configuration guide clarity
- Updated project documentation with more precise instructions
- Added comprehensive troubleshooting guide

### CI/Build

- Improved lint and format commands with silent logging and check modes

## [0.7.5] - 2025-04-14

### Added

- Confirmation prompt before committing to ensure user intent
- Enhanced dry run mode with detailed commit information including file count

### Changed

- Improve display format of generated commit messages using Console and Panel classes
- Refactor commit process code for better readability and maintainability
- Update logging messages to be more informative throughout the commit workflow

### Fixed

- Handle cases where no changes are staged or unstaged by providing clear feedback and exiting early

## [0.7.4] - 2025-04-13

### Added

- Branch coverage configuration for more accurate code coverage reporting

### Changed

- Update code coverage settings to include subdirectories and exclude specific lines
- Modify Flake8 configuration to allow longer line lengths

### Removed

- Redundant bump-my-version configuration from pyproject.toml
- Unnecessary version update configuration for pyproject.toml file

## [0.7.3] - 2025-04-13

### Changed

- Standardize error handling and logging across the application
- Remove redundant quiet mode in favor of logging levels
- Update version configuration to use `__version__.py` instead of `__about__.py`

### Removed

- `src/gac/__about__.py` file in favor of centralized version management

### Fixed

- Update default Groq model identifier in example environment file
- Improve error messages and user feedback for Git and AI operations

## [0.7.2] - 2025-04-13

### Added

- **Repository Context Enrichment**:

  - Intelligent repository context extraction
  - File purpose extraction from docstrings
  - Recent commit history for modified files
  - Repository structure and branch info
  - Example script in `examples/repo_context_example.py`
  - Comprehensive unit tests

- **Configuration Management**:
  - Package-level `config.env` with default model
  - Multi-level config loading:
    1. Project-level `.gac.env`
    2. User-level `~/.gac.env`
    3. Package-level `config.env`
  - New test files for constants and utils

### Changed

- **AI Model Integration**:

  - Robust fallback mechanism for AI model generation
  - Multi-model support with intelligent selection
  - Improved token counting and diff preprocessing

- **Error Handling**:

  - Simplified error paths and recovery mechanisms
  - Enhanced error message display

- **CI/Build**:

  - Updated nightly workflow to 5am Los Angeles
  - Refined workflow triggers
  - Python 3.10 support
  - Improved release and tagging

- **Performance**:
  - Optimized git diff preprocessing
  - Enhanced token counting efficiency

### Removed

- Unnecessary type annotations
- Complex error handling patterns
- Simplified imports

### Documentation

- Comprehensive docstrings
- Repository context enrichment example
- Updated project roadmap

### Security

- Enhanced error handling
- Improved input validation

## [0.7.1] - 2025-04-07

### Added

- Add configuration environment file with default model settings
- Include detailed configuration documentation in installation guide
- Support fallback model configuration in README

### Changed

- Refactor configuration loading to use functional approach
- Update project configuration files to enforce 120 character line length
- Modify release workflow to use semantic versioning and github.ref_name
- Improve error handling and validation in configuration management
- Update README documentation with new features and configurations
- Migrate from markdownlint.yaml to markdownlint-cli2.yaml

### Removed

- Remove complex configuration management logic
- Delete non-existent config wizard references
- Remove unnecessary documentation and test files
- Remove mocking for get_encoding and count_tokens functions in tests
- Delete old markdownlint configuration file

## [0.7.0] - 2025-04-06

### Added

- Support for Ollama AI provider with environment variable management through python-dotenv integration
- Multi-level configuration system supporting environment variables, project-level, user-level, and package-level config files
- Backup AI model functionality with configurable fallback models
- Example model configuration files for major AI providers (Anthropic, OpenAI, Groq, Mistral, Ollama)

### Changed

- Refactor AI-related functionality into consolidated modules with improved error handling
- Simplify main application logic by separating CLI argument parsing from core workflow
- Update line length limit for code formatting from 100 to 120 characters
- Replace multiple AI error subclasses with unified AIError class using error codes
- Enhance configuration wizard to support manual model input and selectable save locations
- Improve commit message generation retry logic and error propagation

### Removed

- Obsolete documentation files (CHANGES.md, DEVELOPMENT.md, REFACTORING.md)
- Deprecated model update script and related README documentation
- Unused demo script and redundant test files
- get_staged_diff() function from git module
- Test mode simulation logic from subprocess handling

### Fixed

- Resolve issue preventing staging when in dry run mode
- Improve remote push validation to prevent false positive status reports

## [0.6.1]

### Added

- **Code Quality**:

  - Markdown linting configuration
  - Prettier configuration
  - VSCode launch configuration
  - Example for diff truncation

- **Testing**:
  - Main module tests
  - AI utility tests
  - Enhanced test coverage

### Changed

- **Code Organization**:

  - Reintroduced AI utilities module
  - Updated test structure
  - Improved error handling

- **Dependencies**:
  - Updated package.json and lock
  - Improved pre-commit hooks

### Fixed

- **Git Operations**:
  - Improved git diff handling
  - Enhanced error recovery

## [0.5.0]

### Added

- **Core Architecture**:

  - New AI module
  - Error handling system
  - File handling utilities
  - Formatting system
  - Prompt template system

- **Testing**:
  - Comprehensive test suite
  - Test fixtures and mocks
  - Error handling tests

### Changed

- **Code Structure**:

  - Major refactoring of core modules
  - Improved error handling
  - Enhanced formatting system

- **Documentation**:
  - Added development guide
  - Added refactoring guide
  - Updated installation guide

### Removed

- Legacy multi-provider examples
- Old changelog preparation scripts
- Old formatting system

## [0.4.3]

### Added

- **Nightly Builds**:

  - GitHub Actions workflow
  - Automated release process

- **Formatting**:

  - New formatting system
  - Support for multiple file types
  - Code formatter integration

- **Testing**:
  - Configuration tests
  - Core module tests
  - Git module tests

### Changed

- **Configuration**:

  - Enhanced config loading
  - Improved environment handling
  - Added constants module

- **Core Functionality**:
  - Improved AI utilities
  - Enhanced git integration
  - Better error handling

## [0.4.2] - 2025-03-30

### Added

- Support for advanced token counting using tiktoken library
- Automated nightly release workflow via GitHub Actions
- Max input tokens configuration option with validation
- Comprehensive test fixtures and mocking configurations

### Changed

- Git diff processing logic to handle large files more effectively
- AI utility functions for more robust token estimation
- Default maximum input token limit increased to 4096
- Subprocess handling and error management in core functionality
- Logging behavior and print statement usage for prompts
- Configuration validation with improved error reporting

### Removed

- File counting logic from formatting functions
- Redundant mock setup code in core tests

## [0.4.1] - 2025-03-29

### Changed

- Update release workflow to install development dependencies and use editable pip installation mode

## [0.4.0] - 2025-03-29

### Added

- Optional hint context support for commit message generation
- New formatting module with dedicated code formatting functions
- GitHub release workflow with automated version bumping and tagging
- Changelog preparation script for release management
- Project description feature to improve commit message context
- Codecov test results upload to CI workflow

### Changed

- Refactored AI provider configuration to use fully qualified model format
- Improved config and core module code quality and structure
- Enhanced git staged files detection to include added, deleted, and renamed files
- Updated version bumping process in Makefile with integrated changelog preparation
- Replaced bumpversion with bump-my-version for version management
- Modified core logic to support one-liner commit messages

### Removed

- run_tests.sh and run_tests.py scripts
- Redundant provider-specific configuration comments from .env.example
- Separate provider and model name configuration options
- Auto changelog generation script call from Makefile bump target

### Fixed

- GAC_MAX_TOKENS validation and error handling with more descriptive messages
- Git staging process to properly handle all file operations and check success
- Commit prompt formatting by removing unnecessary trailing colons
- Default max output tokens reduced from 8192 to 256 for better performance

### Security

- Updated CI workflow to use Python 3.13 environment

## [0.3.0]

### Added

- **Release Automation**:

  - Auto-release script
  - Improved CI workflow

- **Testing**:
  - Enhanced test coverage
  - Improved test fixtures
  - Better test organization

### Changed

- **Code Quality**:
  - Improved error handling
  - Better module organization
  - Enhanced git integration

## [0.2.0]

### Added

- **Core Features**:

  - AI utilities module
  - Configuration system
  - Git integration
  - Comprehensive tests

- **Documentation**:
  - Installation guide
  - How-it-works guide
  - Examples directory

### Changed

- **Project Structure**:
  - Improved module organization
  - Better test structure
  - Enhanced README

## [0.1.0a1] - 2024-12-12

### Added

- Add .windsurfrules to .gitignore
- Add .gac.env.example configuration file
- Add .githooks/check-upstream git hook for upstream change verification
- Add version management system with bumpversion configuration
- Add codecov.yml for code coverage settings

### Changed

- Refactor subprocess handling and logging for improved clarity
- Update pyproject.toml to include gac CLI entry point
- Move hatch configuration from pyproject.toml to hatch.toml
- Update VSCode settings for virtual environment path
- Simplify logging level handling using dynamic logger.log()
- Make verbose output the default and add --quiet flag

### Removed

- Remove redundant git command functions (git_status, git_diff_staged)
- Remove .codeiumignore file

### Fixed

- Fix return type default in run_process() function

## [0.1.0] - Initial Release
