# Git Auto Commit (gac) Project Roadmap

## Current Status

Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit messages based on staged changes. The tool currently supports multiple AI providers including Anthropic Claude, OpenAI, Groq, Mistral, and more.

## Next Steps

### Short-term Goals

1. **Architecture and Code Quality Improvements**

   - [ ] Refactor `core.py` into smaller, focused modules with clear responsibilities
   - [ ] Address f-string linter error in `core.py`
   - [ ] Reduce function complexity, particularly in the `main()` function
   - [x] Standardize error handling across all modules
   - [ ] Implement more consistent parameter naming across functions
   - [ ] Extract duplicated code into reusable helper functions

2. **Performance Optimization**

   - [x] Optimize token usage for large diffs
   - [x] Implement caching for repeated operations
   - [ ] Reduce startup time
   - [ ] Optimize memory usage during diff processing
   - [ ] Improve efficiency of diff processing logic in `git.py`
   - [ ] Enhance cache implementation with thread safety considerations

3. **Improve Error Handling**

   - [x] Add more descriptive error messages
   - [x] Implement graceful fallbacks when API calls fail
   - [x] Add error logging capability
   - [x] Improve error handling for git stash operations
   - [ ] Add more granular error recovery mechanisms
   - [x] Replace empty string returns with proper error objects
   - [x] Improve error message clarity with specific remediation steps
   - [x] Consolidate exception handling patterns

4. **Enhanced Testing**

   - [x] Increase test coverage (cache module now at 93%)
   - [x] Fix core testing infrastructure for cache module
   - [x] Fix test failures in AI utils module
   - [ ] Add integration tests with actual API calls (using mocks)
   - [ ] Create more test fixtures for different git scenarios
   - [ ] Implement property-based testing for commit message generation
   - [x] Add tests for edge cases and error conditions
   - [ ] Add end-to-end workflow tests with real git repositories
   - [ ] Reduce reliance on mocks for more realistic testing

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
   - [ ] Make hard-coded constants configurable (e.g., `MAX_DIFF_TOKENS`)
   - [ ] Implement more robust string processing for commit message cleaning

2. **Provider Expansion**

   - [x] Add initial support for Ollama via configuration
   - [x] Complete Ollama integration with direct API calls
   - [x] Support for Anthropic's Claude 3 Sonnet and Opus
   - [ ] Integrate more specialized code-focused models
   - [ ] Add support for local code analysis models
   - [ ] Implement model performance benchmarking
   - [ ] Improve provider abstraction to reduce provider-specific code
   - [ ] Add automatic fallback to alternative providers on failure

3. **User Experience Improvements**
   - [x] Implement a configuration wizard
   - [x] Add colorized output
   - [x] Create progress indicators for API calls
   - [ ] Add command completion for shells
   - [ ] Develop a web-based configuration interface
   - [ ] Create a VS Code/IDE extension
   - [ ] Simplify model and provider configuration for users
   - [ ] Improve handling of large repositories with better progress indicators
   - [ ] Add detailed debug mode for troubleshooting

## Current Sprint Focus

- Refactor `core.py` into smaller, focused modules
- ~~Standardize error handling across all modules~~ (Completed)
- Address f-string linter error in `core.py`
- Extract duplicated code into reusable helper functions

## Next Sprint Focus

- Improve testing with focus on edge cases and error conditions
- Enhance cache implementation with thread safety
- ~~Replace empty string returns with proper error objects~~ (Completed)
- ~~Improve error message clarity with specific remediation steps~~ (Completed)

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
- Created standardized error handling module with consistent exit codes and user-friendly messages
- Added comprehensive error documentation with examples and best practices
- Implemented test coverage for error handling, including edge cases and error conditions
