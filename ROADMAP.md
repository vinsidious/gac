# Git Auto Commit (gac) Project Roadmap

## Current Status

Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit messages based on staged changes. The tool currently supports multiple AI providers including Anthropic Claude, OpenAI, Groq, Mistral, and more.

## Next Steps

### Short-term Goals

1. **Performance Optimization**

   - [x] Optimize token usage for large diffs
   - [x] Implement caching for repeated operations
   - [ ] Reduce startup time
   - [ ] Optimize memory usage during diff processing

2. **Improve Error Handling**

   - [x] Add more descriptive error messages
   - [x] Implement graceful fallbacks when API calls fail
   - [x] Add error logging capability
   - [x] Improve error handling for git stash operations
   - [ ] Add more granular error recovery mechanisms

3. **Enhanced Testing**
   - [x] Increase test coverage (cache module now at 93%)
   - [x] Fix core testing infrastructure for cache module
   - [x] Fix test failures in AI utils module
   - [ ] Add integration tests with actual API calls (using mocks)
   - [ ] Create more test fixtures for different git scenarios
   - [ ] Implement property-based testing for commit message generation

### Medium-term Goals

1. **Feature Enhancements**

   - [x] Add support for conventional commits format
   - [x] Enhance conventional commit quality to improve structure and detail
   - [x] Improve one-liner commit consistency with the same style conventions as regular messages
   - [x] Improve prompt display formatting
   - [ ] Implement customizable commit templates
   - [ ] Add support for multilingual commit messages
   - [ ] Create interactive mode for refining generated messages
   - [ ] Add semantic versioning support for commit message analysis

2. **Provider Expansion**

   - [x] Add initial support for Ollama via configuration
   - [x] Complete Ollama integration with direct API calls
   - [x] Support for Anthropic's Claude 3 Sonnet and Opus
   - [ ] Integrate more specialized code-focused models
   - [ ] Add support for local code analysis models
   - [ ] Implement model performance benchmarking

3. **User Experience Improvements**
   - [x] Implement a configuration wizard
   - [x] Add colorized output
   - [x] Create progress indicators for API calls
   - [ ] Add command completion for shells
   - [ ] Develop a web-based configuration interface
   - [ ] Create a VS Code/IDE extension

## Current Sprint Focus

- Improve prompt display formatting
- Enhance error handling and recovery
- Optimize memory usage during diff processing

## Next Sprint Focus

- Implement customizable commit templates
- Add semantic versioning support
- Develop a configuration wizard
- Explore IDE extension possibilities

## Completed Items

- Basic implementation with multiple LLM providers
- Command-line interface with various options
- Python file formatting with black and isort
- Interactive prompts for commit and push actions
- Optimized token usage for large diffs with smart truncation and file prioritization
- Support for conventional commits format (--conventional flag)
- Improved error handling with specific error types, better messages, and automatic retries
- Colorized output for better user experience and readability
- Fixed test failures and improved test reliability
- Implemented caching for repeated operations with high test coverage (93%)
- Increased test coverage for core modules
- Fixed git module's project description and staged diff functions
- Improved run_subprocess function to handle errors consistently
- Added dynamic progress indicators for API calls with real-time status updates
- Fixed test failures in AI utils module by improving mocking techniques
- Improved mocking for user input in core module tests with more resilient fixtures
- Added safety mechanism to prevent real git commands during testing
- Enhanced conventional commit message quality with detailed multi-bullet point format
- Added token count display for truncated files to improve diagnostics
- Improved one-liner commit consistency with the same style conventions as regular messages
- Improved error handling for git stash operations
- Added full support for local Ollama models with direct API integration
- Improved prompt display formatting with dynamic "=" underline
- Added visual indicator for LLM prompt creation with emoji and blue info message
