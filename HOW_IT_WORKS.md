# How GAC Works

This document explains the internal architecture of GAC and how it generates commit messages using various AI providers.

## Overview

GAC (Git Auto Commit) streamlines the Git commit process by:

1. Analyzing your staged changes
2. Generating a commit message using an AI provider
3. Formatting code if needed
4. Committing the changes
5. Optionally pushing to the remote repository

## Component Architecture

### Core Components

1. **Command Line Interface (core.py)**

   - Handles command-line arguments and orchestrates the workflow
   - Interacts with Git to get staged changes
   - Handles user interaction

2. **AI Integration (utils.py)**

   - Manages communication with AI providers via aisuite
   - Formats prompts and parses responses
   - Counts tokens to optimize requests

3. **Configuration (config.py)**

   - Manages default settings and environment variables
   - Supports different AI providers and models

4. **Formatting Tools**
   - Integrates with black and isort for Python file formatting

## The Workflow

### 1. Initialization

When you run `gac`, the tool:

- Loads configuration from environment variables and .env file
- Processes command-line arguments
- Checks for staged files

### 2. Code Formatting (Optional)

If enabled and Python files are staged:

- Runs `black` on the Python files
- Runs `isort` on the Python files
- Re-stages the formatted files

### 3. Generating Commit Messages

The tool:

- Gets the staged diff using `git diff --staged`
- Gets the current status using `git status`
- Creates a prompt for the AI model
- Sends the prompt to the configured AI provider
- Receives a structured commit message

### 4. Multi-Provider Support

GAC uses the aisuite library to abstract away provider-specific details:

1. **Provider Selection**

   - Set by `GAC_PROVIDER` environment variable or `--model` flag
   - Each provider needs its own API key

2. **Model Selection**

   - Each provider offers different models
   - Models are referenced using the format `provider:model_name`
   - Default models are defined in `PROVIDER_MODELS` in config.py

3. **Message Generation**
   - The actual AI request is handled by aisuite
   - The prompt template is standardized across providers
   - Token counting ensures requests stay within limits

### 5. Committing Changes

After generating a message:

- The tool displays the suggested commit message
- The user can accept or reject the message
- If accepted, the tool commits the changes using `git commit`
- Optionally pushes the changes using `git push`

## Provider Selection Logic

The logic for selecting a provider and model follows this precedence:

1. Command-line argument (`--model` or `-m`)
2. Environment variable `GAC_MODEL` (fully qualified model)
3. Environment variables `GAC_PROVIDER` and `GAC_MODEL_NAME`
4. Default configuration (Anthropic Claude)

This allows for flexible usage patterns, from project-wide configuration to one-off overrides.

## Provider-Specific Details

### Anthropic Claude (Default)

- Good at understanding code context
- Produces well-structured commit messages
- API charges per token
- Default model: claude-3-haiku

### OpenAI GPT Models

- Fast response times
- Strong code understanding
- Subscription or per-token pricing
- Default model: gpt-4o

### Groq

- Low-latency responses
- Offers LLaMA-based models
- Free tier available
- Default model: llama3-70b-8192

### Mistral

- Range of model sizes
- Good balance of speed and quality
- Competitive pricing
- Default model: mistral-large-latest

### AWS Bedrock

- Access to multiple model families
- AWS infrastructure integration
- Pay-as-you-go pricing
- Default model: meta.llama3-1-70b-instruct-v1:0

### Azure OpenAI

- Enterprise-grade deployment
- Security and compliance features
- Microsoft infrastructure
- Default model: gpt-4

## Prompt Engineering

GAC uses a specific prompt format to guide the AI:

```text
Analyze this git status and git diff and write ONLY a commit message in the following format. Do not include any other text, explanation, or commentary.

Format:
[type]: Short summary of changes (50 chars or less)
 - Bullet point details about the changes
 - Another bullet point if needed

[feat/fix/docs/refactor/test/chore/other]: <description>

Git Status:
...

Git Diff:
...
```

This prompt:

- Provides clear instructions on the desired output format
- Includes both the Git status and diff for context
- Encourages structured, conventional commit messages

## Behind the Scenes: Token Management

GAC includes token counting functionality to:

1. Estimate prompt size before sending
2. Log token usage for monitoring
3. Optimize large diffs to stay within context windows

The token counting is provider-agnostic thanks to aisuite's abstraction layer.

## Environment Variables

GAC uses the following environment variables:

| Variable             | Description       | Example                    |
| -------------------- | ----------------- | -------------------------- |
| `ANTHROPIC_API_KEY`  | Anthropic API key | `sk-ant-api03-...`         |
| `OPENAI_API_KEY`     | OpenAI API key    | `sk-...`                   |
| `GROQ_API_KEY`       | Groq API key      | `gsk_...`                  |
| `MISTRAL_API_KEY`    | Mistral API key   | `...`                      |
| `GAC_PROVIDER`       | Provider to use   | `anthropic`                |
| `GAC_MODEL_NAME`     | Model name        | `claude-3-haiku`           |
| `GAC_MODEL`          | Full model ID     | `anthropic:claude-3-haiku` |
| `GAC_USE_FORMATTING` | Enable formatting | `true`                     |
| `GAC_MAX_TOKENS`     | Max output tokens | `8192`                     |

## Extending GAC

GAC can be extended to support additional providers by:

1. Adding the provider to `PROVIDER_MODELS` in config.py
2. Ensuring aisuite supports the provider
3. Documenting the API key environment variable

No changes to the core logic are needed as long as aisuite supports the provider.
