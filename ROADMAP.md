# Git Auto Commit (gac) Project Roadmap

## Current Status

<<<<<<< Updated upstream

=======

> > > > > > > Stashed changes
> > > > > > > Git Auto Commit (gac) is a CLI tool that uses large language models to generate meaningful commit messages based on staged changes. The tool currently supports multiple AI providers including Anthropic Claude, OpenAI, Groq, Mistral, and more.

## Next Steps

### Short-term Goals

<<<<<<< Updated upstream

1. **Performance Optimization**

=======

1. **Performance Optimization**

   > > > > > > > Stashed changes

   - [x] Optimize token usage for large diffs
   - [ ] Implement caching for repeated operations
   - [ ] Reduce startup time

2. **Improve Error Handling**
   <<<<<<< Updated upstream

=======

> > > > > > > Stashed changes

- [x] Add more descriptive error messages
- [x] Implement graceful fallbacks when API calls fail
- [x] Add error logging capability

3. **Enhanced Testing**
   - [ ] Increase test coverage
   - [ ] Add integration tests with actual API calls (using mocks)
   - [ ] Create more test fixtures for different git scenarios

### Medium-term Goals

<<<<<<< Updated upstream

1. **Feature Enhancements**

=======

1. **Feature Enhancements**

   > > > > > > > Stashed changes

   - [x] Add support for conventional commits format
   - [ ] Implement customizable commit templates
   - [ ] Add support for multilingual commit messages
   - [ ] Create interactive mode for refining generated messages

2. **Provider Expansion**
   <<<<<<< Updated upstream

=======

> > > > > > > Stashed changes

- [ ] Add support for Ollama and local models
- [ ] Support for Anthropic's Claude 3 Sonnet and Opus
- [ ] Integrate more specialized code-focused models

3. **User Experience Improvements**
   - [ ] Implement a configuration wizard
   - [x] Add colorized output
   - [ ] Create progress indicators for API calls
   - [ ] Add command completion for shells

### Long-term Goals

<<<<<<< Updated upstream

1. **Ecosystem Integration**

=======

1. **Ecosystem Integration**

   > > > > > > > Stashed changes

   - [ ] IDE plugins (VS Code, JetBrains)
   - [ ] CI/CD integration
   - [ ] GitHub/GitLab Action

2. **Advanced Features**
   <<<<<<< Updated upstream

=======

> > > > > > > Stashed changes

- [ ] PR description generation
- [ ] Release notes generation
- [ ] Code review suggestions
- [ ] Semantic versioning recommendations

3. **Project Growth**
   - [ ] Documentation website
   - [ ] Community contribution guidelines
   - [ ] Performance benchmarks
   - [ ] Usage analytics (opt-in)

## Current Sprint Focus

<<<<<<< Updated upstream

=======

> > > > > > > Stashed changes

- ~Optimize token usage for large diffs~ ✅ Completed
- ~Add support for conventional commits format~ ✅ Completed
- ~Implement better error handling for API failures~ ✅ Completed
- ~Add colorized output~ ✅ Completed

## Next Sprint Focus

<<<<<<< Updated upstream

=======

> > > > > > > Stashed changes

- Implement caching for repeated operations
- Increase test coverage
- Implement customizable commit templates
- Create progress indicators for API calls

## Completed Items

<<<<<<< Updated upstream

=======

> > > > > > > Stashed changes

- Basic implementation with multiple LLM providers
- Command-line interface with various options
- Python file formatting with black and isort
- Interactive prompts for commit and push actions
- Optimized token usage for large diffs with smart truncation and file prioritization
- Support for conventional commits format (--conventional flag)
- Improved error handling with specific error types, better messages, and automatic retries
  <<<<<<< Updated upstream
- # Colorized output for better user experience and readability
- Colorized output for better user experience and readability
  > > > > > > > Stashed changes
