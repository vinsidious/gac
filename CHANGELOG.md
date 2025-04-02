<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Functional Programming**: Complete architectural redesign around functional programming principles
- **Pure Functions**: Refactored core modules to use pure functions with explicit dependencies
- **Function Composition**: New pipeline approach for the commit workflow
- **Type Hints**: Comprehensive type annotations throughout the codebase
- **Improved Ollama Integration**: Enhanced support for local models
- **Token Management System**: Smarter handling of large diffs with priority-based truncation
- **Progressive Loading**: Show results as they arrive for better UX
- **User-Configurable Prompt Templates**: Allow custom prompt templates via configuration
- **Compatibility Layer**: Added backward compatibility for existing scripts and workflows
- **Advanced Error Recovery**: More robust error handling with fallback strategies

### Changed

- **Simplified Architecture**: Reduced module count and removed unnecessary abstractions
- **Function-Based API**: Replaced class-based approach with simpler functional design
- **Immutable Data Flow**: Changed data handling to prefer immutability
- **Cleaner Git Integration**: Simplified git command abstraction
- **Improved Configuration**: More flexible and explicit configuration management
- **Enhanced Prompt System**: Better prompt generation for model-specific optimization
- **Documentation**: Updated all docs to reflect functional programming approach
- **Developer Experience**: Simplified development setup and contribution workflow
- **Error Messages**: More helpful and actionable error messages
- **Testing**: Shifted focus to behavior-based testing over implementation-based tests

### Removed

- **OOP Abstractions**: Removed unnecessary class hierarchies
- **Redundant Wrappers**: Eliminated redundant wrapper classes
- **Global State**: Reduced reliance on global state and environment variables
- **Dual Interfaces**: Removed dual class/function interfaces for simpler API
- **Legacy Abstractions**: Removed outdated abstractions from earlier versions

## [0.4.4] - 2025-04-01

### Fixed 🐛

- Added missing `questionary` dependency to fix installation issues
- Fixed prompt template not found error by adding default template in package directory

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
