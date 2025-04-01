# Git Auto Commit (gac) Project Roadmap

## Current Status

Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit messages based on staged changes. We're completing a major architectural shift toward functional programming, emphasizing pure functions, immutability, and composability.

## Next Steps

### Short-term Goals

1. **Complete Functional Programming Transition**

   - [x] Redesign core modules around pure functions with explicit dependencies
   - [x] Improve data flow with immutability principles
   - [ ] Replace remaining class-based interfaces with function-based alternatives
   - [ ] Remove all dual implementation patterns
   - [ ] Create a consistent error handling approach based on functional patterns
   - [ ] Apply function composition patterns to key workflows
   - [ ] Add type hints throughout codebase
   - [ ] Refactor prompting system to be more composable

2. **Simplify Core Architecture**

   - [x] Consolidate utility functions into domain-specific modules
   - [x] Remove redundant abstraction layers
   - [ ] Reduce parameter counts in complex functions
   - [ ] Create pipeline helpers for common workflows
   - [ ] Replace environment variable configuration with pure configuration objects
   - [ ] Develop a unified logging strategy compatible with functional paradigm
   - [ ] Extract side effects to the edges of the application
   - [ ] Implement more detailed function documentation

3. **Performance and Reliability Improvements**

   - [x] Optimize token usage for large diffs
   - [x] Implement smarter caching system
   - [ ] Reduce startup time through lazy imports
   - [ ] Implement asynchronous processing where beneficial
   - [ ] Add progressive output for long-running operations
   - [ ] Create more robust connection error handling
   - [ ] Implement request retry mechanisms with backoff
   - [ ] Add filesystem-based fallbacks for network failures

## Current Sprint Focus

- [x] **Function-Based Git Module**: Replace the GitOperationsManager class with pure functions
- [x] **Configuration as Data**: Change configuration handling to use immutable data structures
- [x] **Simpler CLI Interface**: Rework CLI to leverage function-based architecture
- [x] **Reduce Function Parameters**: Use parameter objects for complex functions
- [ ] **Explicit Dependency Injection**: Make dependencies explicit for testing and flexibility
- [ ] **Pure Core Logic**: Move side effects to adapter functions at the edges
- [x] **Update Tests**: Rewrite tests to focus on behaviors rather than implementation details
- [x] **Import Optimization**: Fix circular imports and optimize import structure
- [ ] **Documentation Updates**: Update function docstrings and developer documentation

## Functional Programming Improvements

### Core Principles to Implement

1. **Pure Functions**

   - [x] Extract pure functions for git operations
   - [x] Create pure functions for prompt generation
   - [ ] Refactor AI interaction to be pure
   - [ ] Make file operations composable

2. **Immutable Data Flow**

   - [x] Use immutable data structures for configuration
   - [ ] Implement pipeline pattern for data transformation
   - [ ] Add function composition helpers
   - [ ] Remove in-place modifications

3. **Explicit Dependencies**

   - [ ] Remove implicit dependencies from all functions
   - [ ] Add dependency injection patterns
   - [ ] Create factory functions where appropriate
   - [ ] Add reader monad pattern for configuration

4. **Simplified Testing**
   - [ ] Add property-based testing for pure functions
   - [ ] Reduce test mocking complexity
   - [ ] Create test fixtures for common scenarios
   - [ ] Implement functional testing patterns

## Long-term Vision

Our simplified vision is to:

1. **Core Functionality**: Generate excellent commit messages using AI with minimal complexity
2. **Functional Purity**: Maintain high functional purity for maintainability and reliability
3. **Developer Experience**: Provide a consistent and intuitive API for developers
4. **Performance**: Optimize for speed and efficiency in the commit workflow
5. **Extensibility**: Create a plugin architecture for extending functionality

## Explicitly Not Planned

We've decided against these items to maintain focus:

- ~~Adding new AI providers (will maintain current providers only)~~
- ~~Command completion for shells~~
- ~~Web-based configuration interface~~
- ~~VS Code/IDE extensions~~
- ~~Interactive mode for refining generated messages~~
- ~~Semantic versioning support~~
- ~~Multilingual commit messages~~
- ~~Complex class hierarchies and abstractions~~
- ~~Refactoring to more "elegant" but harder-to-maintain patterns~~
- ~~Create a pipeline factory for the commit workflow~~

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
- [x] Added push functionality to push changes to remote after committing
- [x] Shifted from OOP to a more functional programming approach
- [x] Reorganized code into focused modules with clear responsibilities
- [x] Added compatibility layer to ensure existing code continues to work
