# Git Auto Commit (gac) Project Roadmap

## Current Status

Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit
messages based on staged changes. We have completed a major architectural shift toward functional
programming, emphasizing pure functions, immutability, and composability. The codebase now follows a
functional paradigm with improved type hints, better error handling, and a more streamlined
architecture. We have significantly improved test coverage, particularly for the main.py and ai.py
modules. The codebase has been simplified by removing deprecated functions and unnecessary
parameters.

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
   - [x] Implement smart truncation for git diffs
   - [x] Add token counting mechanism for different AI models
   - [x] Create more robust connection error handling
   - [x] Implement request retry mechanisms with backoff
   - [ ] Add filesystem-based fallbacks for network failures
   - [ ] Improve performance for large repositories

4. **Usability and Customization** ✅

   - [x] Implement template-based prompt system
   - [x] Add support for user-configurable prompts
   - [x] Create better documentation for template customization

5. **User Experience Improvements** 🔄

   - [x] Replace custom spinner with Halo for better progress indication
   - [x] Progressive loading of AI responses
   - [ ] Add interactive mode for refining generated messages
   - [x] Implement better error recovery for failed API calls
   - [ ] Create better visualization of diff context

## Current Sprint Focus

- [x] **Function-Based Git Module**: Replace the GitOperationsManager class with pure functions
- [x] **Configuration as Data**: Change configuration handling to use immutable data structures
- [x] **Simpler CLI Interface**: Rework CLI to leverage function-based architecture
- [x] **Streamlined Command Interface**: Replace subcommand structure with a single main function
- [x] **Reduce Function Parameters**: Use parameter objects for complex functions
- [x] **Explicit Dependency Injection**: Make dependencies explicit for testing and flexibility
- [x] **Pure Core Logic**: Move side effects to adapter functions at the edges
- [x] **Update Tests**: Rewrite tests to focus on behaviors rather than implementation details
- [x] **Import Optimization**: Fix circular imports and optimize import structure
- [x] **Documentation Updates**: Update function docstrings and developer documentation
- [x] **Customizable Prompts**: Add support for user-provided prompt templates

## Next Sprint (Q3 2023)

- [x] **Quiet Mode Improvements**: Add `-q` flag to suppress non-essential output while maintaining
      commit message visibility
- [x] **Enhanced Token Optimization**:
  - [x] Implement advanced token usage strategies
  - [x] Add configurable token limit settings
  - [x] Develop intelligent diff truncation algorithms
- [x] **Enhanced Error Recovery**: Implement robust error handling for network failures
- [x] **Request Retry System**: Add automatic retries with backoff for API calls
- [ ] **Interactive Mode**: Create an interactive mode to review and refine generated messages
- [ ] **Performance Optimization**: Improve token usage and processing for large repositories
- [x] **CLI UX Improvements**: Better formatting of diffs and visualization of changes
- [ ] **Plugin Architecture**: Design an extensible plugin system for custom integrations
- [ ] **Local Model Support**: Enhanced support for running with local LLMs

## Next Sprint (Q2 2024)

- [ ] **Interactive Mode Implementation**:
  - [ ] Add optional interactive review of generated commit messages
  - [ ] Implement message editing capabilities
  - [ ] Create workflow for refining messages with AI assistance
- [ ] **Performance Optimization for Large Repositories**:
  - [ ] Implement selective diff processing
  - [ ] Add heuristic-based file prioritization
  - [ ] Optimize memory usage for large diffs
- [ ] **Plugin System Development**:
  - [ ] Design extensible plugin architecture
  - [ ] Create plugin discovery mechanism
  - [ ] Implement standard plugin interface
  - [ ] Develop documentation for plugin creation
- [ ] **Local LLM Integration Improvements**:
  - [ ] Enhance support for popular local models
  - [ ] Add configuration options for local model parameters
  - [ ] Implement better error handling for local model failures
- [ ] **Advanced Diff Visualization**:
  - [ ] Improve contextual display of changes
  - [ ] Add file-specific formatting options
  - [ ] Create summarized view for large diffs

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

- ~~CLI subcommand structure (gac commit, gac config, etc.)~~
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
- ~~Caching mechanisms of any kind~~ - We will NEVER implement caching since it is of minimal
  benefit in our use case where text content rarely repeats

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
- [x] Added dynamic progress indicators for API calls
- [x] Added full support for local Ollama models with direct API integration
- [x] Removed core.py entirely as it was just a wrapper
- [x] Simplified main.py to be a direct command implementation with no subcommands
- [x] Added push functionality to push changes to remote after committing
- [x] Shifted from OOP to a more functional programming approach
- [x] Reorganized code into focused modules with clear responsibilities
- [x] Added compatibility layer to ensure existing code continues to work
- [x] Implemented dictionary-based options pattern for parameter management
- [x] Added functional error handling with decorators and helper functions
- [x] Created function composition helpers for git operations
- [x] Implemented a pure functional workflow API
- [x] Removed all caching mechanisms as they provide minimal benefit for our use case
- [x] Implemented advanced token usage optimization
  - Smart truncation for git diffs
  - Intelligent token counting for different AI models
  - Handling of large file diffs with token-aware truncation
- [x] Added quiet mode with refined output control
  - Suppress non-essential messages
  - Maintain commit message panel visibility
  - Respect user's desire for minimal output
- [x] Improved model selection and configuration
  - Better handling of provider:model format
  - Enhanced configuration flexibility
- [x] Refined error handling and logging
  - More precise error messages
  - Better logging control
- [x] Continued functional programming improvements
  - Simplified parameter management
  - Enhanced error handling decorators
- [x] Added model fallback mechanism
  - Configurable backup model support
  - Graceful fallback in case of primary model failure
- [x] Enhanced CLI interface
  - Added dry-run mode
  - Improved error messaging
  - Better progress indicators

## Token Optimization Strategy

### Current Implementation

Our token optimization strategy focuses on intelligent handling of large diffs and AI model
interactions:

1. **Smart Truncation**

   - Dynamically truncate git diffs based on token limits
   - Preserve critical context while reducing overall token count
   - Implement model-specific tokenization strategies

2. **Intelligent Token Counting**

   - Use `tiktoken` for accurate token counting across different models
   - Support multiple encoding strategies (Claude, OpenAI, etc.)
   - Dynamically select appropriate tokenization method

3. **Diff Processing**
   - Prioritize meaningful changes over large, auto-generated files
   - Skip known large file patterns (lock files, build artifacts)
   - Implement token-aware diff selection

### Future Enhancements

- Develop additional configurable token limit settings
- Create more adaptive truncation algorithms
- Improve context preservation during diff reduction
- Add support for more AI model tokenization strategies

### Technical Challenges

- Maintaining semantic meaning while reducing token count
- Handling diverse file types and programming languages
- Balancing performance with comprehensive context

### Guiding Principles

- Minimize token usage without losing critical information
- Provide transparent, predictable truncation
- Support multiple AI providers with different tokenization methods
