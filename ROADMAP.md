# Git Auto Commit (gac) Project Roadmap

## Current Status

Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit messages based on staged changes. We have completed a major architectural shift toward functional programming, emphasizing pure functions, immutability, and composability. The codebase now follows a functional paradigm with improved type hints, better error handling, and a more streamlined architecture.

## Next Steps

### Short-term Goals

1. **Complete Functional Programming Transition** ✅

   - [x] Redesign core modules around pure functions with explicit dependencies
   - [x] Improve data flow with immutability principles
   - [x] Replace remaining class-based interfaces with function-based alternatives
   - [x] Remove all dual implementation patterns
   - [x] Create a consistent error handling approach based on functional patterns

2. **Simplify Core Architecture** ✅

   - [x] Consolidate utility functions into domain-specific modules
   - [x] Remove redundant abstraction layers
   - [x] Reduce parameter counts in complex functions
   - [x] Create pipeline helpers for common workflows
   - [x] Replace environment variable configuration with pure configuration objects
   - [x] Develop a unified logging strategy compatible with functional paradigm
   - [x] Extract side effects to the edges of the application
   - [x] Implement more detailed function documentation

3. **Performance and Reliability Improvements** 🔄

   - [x] Optimize token usage for large diffs
   - [x] Implement smarter caching system
   - [ ] Create more robust connection error handling
   - [ ] Implement request retry mechanisms with backoff
   - [ ] Add filesystem-based fallbacks for network failures
   - [ ] Improve performance for large repositories

4. **Usability and Customization** ✅

   - [x] Implement template-based prompt system
   - [x] Add support for user-configurable prompts
   - [x] Create better documentation for template customization

5. **User Experience Improvements** 🆕

   - [x] Replace custom spinner with Halo for better progress indication
   - [x] Progressive loading of AI responses
   - [ ] Add interactive mode for refining generated messages
   - [ ] Implement better error recovery for failed API calls
   - [ ] Create better visualization of diff context

## Current Sprint Focus

- [x] **Function-Based Git Module**: Replace the GitOperationsManager class with pure functions
- [x] **Configuration as Data**: Change configuration handling to use immutable data structures
- [x] **Simpler CLI Interface**: Rework CLI to leverage function-based architecture
- [x] **Reduce Function Parameters**: Use parameter objects for complex functions
- [x] **Explicit Dependency Injection**: Make dependencies explicit for testing and flexibility
- [x] **Pure Core Logic**: Move side effects to adapter functions at the edges
- [x] **Update Tests**: Rewrite tests to focus on behaviors rather than implementation details
- [x] **Import Optimization**: Fix circular imports and optimize import structure
- [x] **Documentation Updates**: Update function docstrings and developer documentation
- [x] **Customizable Prompts**: Add support for user-provided prompt templates

## Next Sprint (Q2 2025)

- [ ] **Enhanced Error Recovery**: Implement robust error handling for network failures
- [ ] **Request Retry System**: Add automatic retries with backoff for API calls
- [ ] **Interactive Mode**: Create an interactive mode to review and refine generated messages
- [ ] **Performance Optimization**: Improve token usage and processing for large repositories
- [ ] **CLI UX Improvements**: Better formatting of diffs and visualization of changes
- [ ] **Plugin Architecture**: Design an extensible plugin system for custom integrations
- [ ] **Local Model Support**: Enhanced support for running with local LLMs

## Functional Programming Improvements

### Core Principles Implemented ✅

1. **Pure Functions**

   - [x] Extract pure functions for git operations
   - [x] Create pure functions for prompt generation
   - [x] Create functional error handling patterns with function decorators
   - [x] Create function composition helpers

2. **Immutable Data Flow**

   - [x] Use immutable dictionaries for configuration
   - [x] Remove in-place modifications
   - [x] Implement option creation functions
   - [x] Use result dictionaries for complex operations

3. **Simplified Testing**
   - [x] Add property-based testing for pure functions
   - [x] Reduce test mocking complexity
   - [x] Create test fixtures for common scenarios
   - [x] Implement functional testing patterns

## Long-term Vision

Our simplified vision is to:

1. **Core Functionality**: Generate excellent commit messages using AI with minimal complexity
2. **Functional Purity**: Maintain high functional purity for maintainability and reliability
3. **Developer Experience**: Provide a consistent and intuitive API for developers
4. **Performance**: Optimize for speed and efficiency in the commit workflow
5. **Extensibility**: Create a plugin architecture for extending functionality
6. **Customization**: Add support for user-defined prompt templates and configuration

## Explicitly Not Planned

We've decided against these items to maintain focus:

- ~~Command completion for shells~~
- ~~Web-based configuration interface~~
- ~~VS Code/IDE extensions~~
- ~~Semantic versioning support~~
- ~~Multilingual commit messages~~
- ~~Complex class hierarchies and abstractions~~
- ~~Refactoring to more "elegant" but harder-to-maintain patterns~~
- ~~Create a pipeline factory for the commit workflow~~
- ~~Implement pipeline pattern for data transformation~~
- ~~Reduce startup time through lazy imports~~

## Reconsidered Items

Items we originally ruled out but have reconsidered:

- **Adding new AI providers**: Will selectively add support for promising new models
- **Interactive mode**: Planning to add limited interactive refinement capability
- **Request retry mechanisms**: Will implement to improve reliability

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
- [x] Implemented dictionary-based options pattern for parameter management
- [x] Added functional error handling with decorators and helper functions
- [x] Created function composition helpers for git operations
- [x] Implemented a pure functional workflow API
