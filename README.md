# Git Auto Commit (GAC) 🚀

[![Tests](https://github.com/cellwebb/gac/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/gac/actions/workflows/ci.yml)
[![Code Coverage](https://codecov.io/gh/cellwebb/gac/graph/badge.svg?token=WXOSX7R2JH)](https://codecov.io/gh/cellwebb/gac)
[![PyPI - Version](https://img.shields.io/pypi/v/gac.svg)](https://pypi.org/project/gac)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gac.svg)](https://pypi.org/project/gac)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 What is GAC?

Git Auto Commit (GAC) is an intelligent CLI tool that leverages AI to generate meaningful,
context-aware commit messages based on your staged changes. Built with functional programming
principles, GAC simplifies your Git workflow by automatically crafting descriptive commit messages.

## ✨ Key Features

- 🤖 AI-Generated Commit Messages
- 🧩 Multi-Provider API Support (Anthropic, OpenAI, Groq, Mistral)
- 🌐 Local Model Integration (Ollama)
- 🔧 Automatic Code Formatting
- 🚀 Functional Programming Design
- 🔄 Fallback Model Support

## 🔌 Development Status

This project is under active development and not yet available via package managers. To try it out:

```bash
# Clone the repository
git clone https://github.com/cellwebb/gac.git
cd gac

# Install in development mode
pip install -e .
```

## Installation

### Using pipx (recommended)

To install directly from GitHub:

```bash
pipx install git+https://github.com/cellwebb/gac.git
```

For a specific version or branch:

```bash
pipx install git+https://github.com/cellwebb/gac.git@branch-or-tag
```

## 🎬 Usage

1. Stage your changes:

```bash
git add .
```

2. Generate a commit message:

```bash
gac
```

## 🛠 Configuration

### AI Provider Setup

1. Get an API key from your preferred provider
2. Set the environment variables in your `.gac.env` file:

```bash
# Primary model configuration
GAC_MODEL=groq:meta-llama/llama-4-scout-17b-16e-instruct
GROQ_API_KEY=your_key_here

# Backup model configuration
GAC_BACKUP_MODEL=anthropic:claude-3-5-haiku-latest
ANTHROPIC_API_KEY=your_key_here

# Or use local models with Ollama
# GAC_MODEL=ollama:llama4

# Aditional providers: Mistral, OpenAI
```

### Interactive Configuration

```bash
# Run configuration wizard
gac --config
```

The configuration wizard guides you through selecting:

- Your preferred AI provider
- The specific model to use
- Code formatting preferences

Your choices are automatically saved to a `.gac.env` file in your home directory, making them
persistent across terminal sessions.

### Configuration Files

GAC supports several configuration locations with the following precedence (highest to lowest):

1. Environment variables in your current shell session
2. Project-level `.gac.env` file in your current directory
3. User-level `.gac.env` file in your home directory
4. Package-level `config.env` file (installed with the module)
5. Default built-in values

This multi-level configuration system allows for shared team settings in the package, user
preferences in the home directory, and project-specific overrides in each repository.

## 🌈 Advanced Usage

```bash
# Stage all changes and commit
gac -a

# Automatically confirm suggested commit message (use at your own risk)
gac -f

# Automatically push after committing (use at your own risk)
gac -p

# Generate one-line commit message
gac -o

# Dry run mode (format and generate message without staging or committing)
gac --dry-run

# Provide context hint
gac -h \"Fix authentication bug\"

# All together now
gac -afpo -h \"Fixing JIRA ticket #420\"
```

## 🔌 Supported Providers

- Anthropic
- OpenAI
- Groq
- Mistral
- Local Models (Ollama)

## 📚 Documentation

- [Installation Guide](INSTALLATION.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License. See [LICENSE.txt](LICENSE.txt) for details.

## 🌍 Community

- Report bugs: [GitHub Issues](https://github.com/cellwebb/gac/issues)
- Discussions: [GitHub Discussions](https://github.com/cellwebb/gac/discussions)

## 💡 Roadmap

Check out our [ROADMAP.md](ROADMAP.md) to see planned features and improvements.
