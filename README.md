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
- 🧩 Multi-Provider Support (Anthropic, OpenAI, Groq, Mistral)
- 🌐 Local Model Integration (Ollama)
- 🔧 Automatic Code Formatting
- 🚀 Functional Programming Design
- 🔒 Secure and Configurable
- 🐍 Python 3.10+ Compatibility

## 🚀 Quick Installation

```bash
# Recommended method
pipx install gac

# Alternative: pip installation
pip install gac
```

## 🎬 Quick Start

1. Stage your changes:

```bash
git add .
```

2. Generate a commit message:

```bash
gac
```

## 🛠 Configuration Options

### AI Provider Setup

1. Get an API key from your preferred provider
2. Set the environment variable:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Interactive Configuration

```bash
# Run configuration wizard
gac --config-wizard
```

## 🌈 Advanced Usage

```bash
# Stage all changes and commit
gac -a

# Use a specific AI model
gac -m openai:gpt-4o

# Generate one-line commit message
gac -o

# Provide context hint
gac -h "Fix authentication bug"
```

## 🔌 Supported Providers

- Anthropic Claude
- OpenAI GPT
- Groq
- Mistral
- Local Models (Ollama)

## 📚 Documentation

- [Installation Guide](INSTALLATION.md)
- [Development Guide](DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)

## 🤝 Contributing

Contributions are welcome! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for guidelines.

## 📝 License

MIT License. See [LICENSE.txt](LICENSE.txt) for details.

## 🌍 Community

- Report bugs: [GitHub Issues](https://github.com/cellwebb/gac/issues)
- Discussions: [GitHub Discussions](https://github.com/cellwebb/gac/discussions)

## 💡 Roadmap

Check out our [ROADMAP.md](ROADMAP.md) to see planned features and improvements.

## 🙌 Acknowledgements

- Powered by functional programming principles
- Inspired by the need for smarter commit workflows
