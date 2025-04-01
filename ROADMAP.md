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
   - [x] Extract logging configuration into a dedicated utility function
   - [x] Merge git.py and git_operations.py to eliminate duplication
   - [x] Eliminate delegation pattern in git.py to reduce unnecessary indirection
   - [ ] Break down the large CommitWorkflow class into smaller components
   - [ ] Simplify OOP approach - consider more functional patterns where appropriate
   - [x] Simplify formatting architecture using a more direct approach
   - [ ] Centralize error handling and reduce duplication
   - [ ] Reduce the error type hierarchy - streamline to essential types only

2. **Performance Optimization**

   - [x] Optimize token usage for large diffs
   - [x] Implement caching for repeated operations
   - [ ] Reduce startup time
   - [ ] Optimize memory usage during diff processing
   - [x] Improve efficiency of diff processing logic in `git.py`

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

- [x] Add push functionality to enable pushing changes after committing
- [x] Merge git.py and git_operations.py into a single, simpler module
- [x] Improve workflow.py to use simplified git functionality directly
- [x] Complete the further simplification of workflow.py by breaking it into smaller components
- [x] Reduce abstraction layers throughout the codebase
- [x] Consolidate provider handling logic between ai_utils.py and commit_manager.py
- [x] Replace class-based architecture with a simpler functional approach
- [x] Reorganize code into focused modules with clear responsibilities
- [x] Provide backward compatibility layer for existing code and tests
- [ ] Update tests to work with the new functional API

## Recent Improvements

### Simplified Architecture

We've implemented a significant architectural improvement to simplify the codebase:

1. **Simplified Module Structure**

   - Reorganized code into focused modules with clear responsibilities
   - Added compatibility layer to ensure existing code and tests continue to work
   - Implemented a function-based API to replace the class-based architecture

2. **Reduced Dependencies**

   - Minimized dependencies between modules
   - Made each module have a clear, focused responsibility
   - Improved separation of concerns

3. **Better Error Handling**
   - Streamlined error hierarchy
   - Provided better error messages with remediation steps
   - Improved error handling patterns

### Git and Workflow Simplification

We've made several significant improvements to simplify the codebase:

1. **Consolidated Git Functionality**

   - Merged git.py and git_operations.py into a single module
   - Removed duplicate code and unnecessary abstraction layers
   - Implemented a functional approach with a compatibility wrapper for existing class-based code

2. **Improved Prompt System**

   - Simplified the template generation in prompts.py
   - Added better error handling for malformed commit messages
   - Improved clean_commit_message to handle more edge cases

3. **Streamlined Workflow**
   - Updated workflow.py to use git functions directly instead of through manager classes
   - Simplified the formatting and re-staging process
   - Improved error handling and added better user feedback

## Long-term Vision

Our simplified vision is to focus on:

1. **Core Functionality**: Generate excellent commit messages using AI
2. **Simplicity**: Maintain a clean, easy-to-understand codebase
3. **Reliability**: Ensure the tool works consistently across environments
4. **Maintainability**: Keep the code easy for a single person to maintain and understand

## Explicitly Not Planned

We've decided against these items to maintain a focused, streamlined tool:

- ~~Adding new AI providers (will maintain current providers only)~~
- ~~Command completion for shells~~
- ~~Web-based configuration interface~~
- ~~VS Code/IDE extensions~~
- ~~Interactive mode for refining generated messages~~
- ~~Semantic versioning support~~
- ~~Multilingual commit messages~~
- ~~Complex class hierarchies and abstractions~~
- ~~Refactoring to more "elegant" but harder-to-maintain patterns~~

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
- [x] Added push functionality to push changes to remote after committing
- [x] Simplified architecture with function-based API instead of class-based approach
- [x] Reorganized code into focused modules with clear responsibilities
- [x] Added compatibility layer to ensure existing code continues to work
