# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!-- New changes go here -->

## [0.1.0] - 2025-03-24

### Changed

- Migrated from `hatch` to `uv` for package management.
- Updated development workflow to use `Makefile` for common tasks.
- Improved development environment setup.

## [0.1.0a1] - 2024-12-12

### Added

- Initial release of gac CLI tool
- Core functionality to generate commit messages using Claude AI
- Automatic code formatting with black and isort
- Interactive commit and push workflow
- Command line options:
  - `--test`: Run in test mode
  - `--force, -f`: Skip all prompts
  - `--add-all, -a`: Stage all changes
- Local development environment configuration with hatch
- VSCode integration and settings
- Comprehensive documentation in README.md

[0.1.0]: https://github.com/cellwebb/gac/releases/tag/v0.1.0
[0.1.0a1]: https://github.com/cellwebb/gac/releases/tag/v0.1.0a1
