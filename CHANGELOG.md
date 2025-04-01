<!-- markdownlint-disable MD024-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support for local LLMs through Ollama integration
- Support for conventional commits format with `--conventional` flag
- Implemented caching for repeated operations to improve performance
- Added functions to detect Ollama availability and check for specific models
- Increased default token limits: per-file limit to 2500 (from 1000) and overall input limit to 16000 (from 4096)
- Better error handling with specific error types
- Automatic retries for transient API errors
- Added token count display for truncated files to help diagnose and manage large diffs
- Added `--no-cache` and `--clear-cache` options to CLI
- Colorized terminal output for better readability and user experience
- Safety mechanism to prevent real git commands from running during tests
- Interactive configuration wizard (`gac --config-wizard`) to simplify provider and model selection
- Support for configuration via environment variables
- Expanded documentation for configuration options
- Added `--push` (`-p`) option to push changes to remote after committing

### Changed

- Improved prompt display with new `--show-prompt` (abbreviated) and `--show-prompt-full` flags
- Enhanced conventional commit format to include better structure with bullet points for detailed descriptions
- Strengthened conventional commit prompt to ensure detailed, multi-bullet point commit messages
- Improved commit messages by ordering bullet points from most important to least important
- Improved token usage optimization for large diffs
- Improved truncated file display with specific token counts for each file
- Refactored git operations to take advantage of caching
- Enhanced error messages with more descriptive information
- Updated test suite for better reliability and coverage
- Improved mocking for user input in core module tests with more resilient fixtures
- Improved configuration handling with more robust validation
- Updated README with configuration wizard instructions

### Fixed

- Fixed test inconsistencies with run_subprocess functions
- Corrected prompt generation for hints
- Fixed git module test issues with cached functions
- Enhanced backtick cleaning to prevent code block markers in individual bullet points

## [0.4.3] - 2025-03-30

### Added 🚀

- New code formatters for JavaScript, TypeScript, Markdown, HTML, CSS, JSON, YAML, Rust, and Go
- Support for splitting simulation mode and test mode with all-caps labeling

### Changed 🔧

- Refactored `ai_utils.py` with improved token counting and encoding detection
- Simplified constants and git module imports
- Enhanced formatting system with optimized file detection and formatter integration
- Removed pytest's `--no-cov` flag in configuration

### Improved 🌟

- Increased test coverage to 94%
- Streamlined configuration and formatting modules

### Refactored 🔨

- Updated `main()` to support enhanced formatting system for all file types
- Simplified git module functions and added more robust file handling

## [0.4.2] - 2025-03-31

### Added 🚀

- **Tiktoken integration** for advanced token counting and model-specific encoding support
- Enhanced large file handling in git diff processing

### Changed 🔧

- Improved token counting logic using tiktoken for more accurate token estimation
- Refactored git diff handling to manage large files and reduce token usage
- Updated AI utility functions to support better token counting across different models

### Fixed 🐛

- Refined token counting algorithm to handle various input types and models
- Improved subprocess error handling in git diff processing
- Enhanced test coverage for token counting and git utilities

### Refactored 🛠️

- Restructured AI utility functions for more robust token counting
- Simplified git diff processing with better large file detection
- Updated test fixtures to support new token counting methods

## [0.4.1] - 2025-03-29

### Bug Fixes

- fix release workflow to use pip install -e ".[dev]" instead of requirements.txt

## [0.4.0] - 2025-03-29

### Added

- 🌟 Enhanced project description retrieval for improved commit message context
- 🔄 Added optional hint context for commit messages
- 📝 Added one-liner commit message generation option
- 🔍 Added support for simulated files in test mode
- 🚀 Created changelog preparation script for release management
- 🔧 Added formatting module with code extraction

### Changed

- 🛠️ Refactored git status detection and file handling methods
- 💡 Updated multi-provider examples with latest model names
- 📊 Reduced default max output tokens from 8192 to 512
- 🔄 Switched from `bumpversion` to `bump-my-version` for version management
- 🧩 Enhanced test mode with real diff and simulation support
- 📝 Updated `.env.example` configuration details

### Removed

- 🗑️ Deleted `run_tests.sh` and `run_tests.py` scripts

### Fixed

- 🐛 Improve git staged files detection and staging
- 🔧 Remove colon from commit prompts
- 📝 Enhance token parsing and validation in configuration
- 🛡️ Improve error handling in configuration and core modules

### Security

- 📦 Enhanced version bumping and release processes in CI/CD workflows
- 🔐 Added GitHub release workflow with version management

## [0.3.1] - 2025-03-27

### Added

- 🌟 Enhanced project description retrieval feature to improve context for commit messages
- 📝 Added option for generating one-liner commit messages
- ✅ Added Codecov test results upload to CI workflow
- 📝 Created `conftest.py` to improve test configuration and module importing

### Changed

- 🔧 Updated CI workflow to use Python 3.13
- 🛠️ Switched from `bumpversion` to `bump-my-version` for version management
- 📊 Updated coverage configuration and test reporting
- 💡 Enhanced `send_to_llm()` function with optional one-liner commit message generation
- 📉 Reduced default max output tokens from 8192 to 512
- 🔍 Updated multi-provider examples with latest model names

### Removed

- 🗑️ Deleted `run_tests.sh` and `run_tests.py` scripts

### Fixed

- 🐛 Improve git staged files detection and staging
- 🔧 Remove colon from commit prompts
- 📝 Enhance token parsing and validation in configuration
- 🛡️ Improve error handling in configuration and core modules
