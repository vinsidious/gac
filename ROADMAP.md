# Git Auto Commit (gac) Project Roadmap

## Current Status

Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit messages based on staged changes. We're currently focusing on simplification and streamlining the core functionality.

## Next Steps

### Short-term Goals

1. **Architecture and Code Simplification**

   - [x] Remove core.py entirely (it was just a wrapper around cli.py)
   - [x] Consolidate main.py and cli.py to reduce duplication
   - [x] Remove the edit option for commit messages
   - [x] Remove the test mode flag which caused confusion
   - [ ] Extract logging configuration into a dedicated utility function
   - [ ] Break down the large CommitWorkflow class into smaller components
   - [ ] Simplify formatting architecture using a more direct approach
   - [ ] Centralize error handling and reduce duplication

2. **Performance Optimization**

   - [x] Optimize token usage for large diffs
   - [x] Implement caching for repeated operations
   - [ ] Reduce startup time
   - [ ] Optimize memory usage during diff processing
   - [ ] Improve efficiency of diff processing logic in `git.py`

3. **Improve Error Handling**

   - [x] Add more descriptive error messages
   - [x] Implement graceful fallbacks when API calls fail
   - [x] Add error logging capability
   - [x] Improve error handling for git stash operations
   - [ ] Add more granular error recovery mechanisms
   - [x] Replace empty string returns with proper error objects
   - [ ] Improve error message clarity with specific remediation steps
   - [ ] Consolidate exception handling patterns

## Current Sprint Focus

- [ ] Complete the simplification of workflow.py by breaking it into smaller components
- [ ] Integrate the new commit_manager.py and git_operations.py files
- [ ] Ensure all entry points use the centralized logging configuration
- [ ] Remove redundant compatibility functions once testing is updated

## Long-term Vision

Our simplified vision is to focus on:

1. **Core Functionality**: Generate excellent commit messages using AI
2. **Simplicity**: Maintain a clean, easy-to-understand codebase
3. **Reliability**: Ensure the tool works consistently across environments

## Explicitly Not Planned

We've decided against these items to maintain a focused, streamlined tool:

- ~~Adding new AI providers (will maintain current providers only)~~
- ~~Command completion for shells~~
- ~~Web-based configuration interface~~
- ~~VS Code/IDE extensions~~
- ~~Interactive mode for refining generated messages~~
- ~~Semantic versioning support~~
- ~~Multilingual commit messages~~

## Completed Items

- [x] Basic implementation with multiple LLM providers
- [x] Command-line interface with various options
- [x] Interactive prompts for commit actions
- [x] Optimized token usage for large diffs with smart truncation and file prioritization
- [x] Support for conventional commits format (--conventional flag)
- [x] Improved error handling with specific error types and better messages
- [x] Colorized output for better user experience and readability
- [x] Implemented caching for repeated operations
- [x] Added dynamic progress indicators for API calls
- [x] Added full support for local Ollama models with direct API integration
- [x] Removed core.py entirely as it was just a wrapper
- [x] Simplified main.py to be a lightweight compatibility wrapper around cli.py
- [x] Extracted commit message generation into a separate CommitManager class
- [x] Extracted git operations into a separate GitOperationsManager class
- [x] Removed the edit option from commit messages to simplify the workflow
- [x] Removed the confusing test mode flag
