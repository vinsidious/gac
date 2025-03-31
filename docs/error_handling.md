# Error Handling in GAC

This document describes the standardized error handling approach in the GAC codebase, including available error types and best practices for error management.

## Overview

The `gac.errors` module provides a consistent error handling framework for the entire application. Key features include:

- Hierarchical error type system
- Standardized error handling with appropriate exit codes
- User-friendly error messages with remediation steps
- Conversion utilities for external exceptions

## Error Types

All GAC-specific errors inherit from the base `GACError` class:

```test
Exception
  └── GACError
       ├── ConfigError
       ├── GitError
       ├── AIProviderError
       │    ├── AIConnectionError
       │    ├── AIAuthenticationError
       │    ├── AIRateLimitError
       │    ├── AITimeoutError
       │    └── AIModelError
       ├── FormattingError
       └── CacheError
```

Each error type has a specific exit code to help identify the source of failures:

| Error Type | Exit Code | Description |
|------------|-----------|-------------|
| GACError | 1 | Base exception for all GAC errors |
| ConfigError | 2 | Configuration issues |
| GitError | 3 | Git operation problems |
| AIProviderError | 4 | Base class for AI provider errors |
| AIConnectionError | 5 | Network/connectivity issues |
| AIAuthenticationError | 6 | API key/auth problems |
| AIRateLimitError | 7 | API rate limits exceeded |
| AITimeoutError | 8 | API call timeout |
| AIModelError | 9 | Model specification issues |
| FormattingError | 10 | Code formatting problems |
| CacheError | 11 | Cache operation failures |

## Using Error Types

When raising errors in the codebase, use the most specific error type available:

```python
from gac.errors import ConfigError, GitError

# Example of raising a config error
if not config.get("model"):
    raise ConfigError("Model not specified in configuration")

# Example of raising a git error
if not os.path.exists(".git"):
    raise GitError("Not in a git repository")
```

## Error Handling Functions

### handle_error

The `handle_error` function provides a central way to handle exceptions:

```python
from gac.errors import handle_error, GitError

try:
    # Some code that might fail
    run_git_command()
except Exception as e:
    # Handle the error with standardized logging and user feedback
    handle_error(e, quiet=False, exit_program=True)
```

Parameters:

- `error`: The exception to handle
- `quiet`: If True, suppress console output (default: False)
- `exit_program`: If True, exit with the appropriate code (default: True)

### format_error_for_user

This function formats errors with user-friendly messages and remediation steps:

```python
from gac.errors import format_error_for_user, AIConnectionError

error = AIConnectionError("Failed to connect to API")
message = format_error_for_user(error)
print(message)
# Output:
# Failed to connect to API
# 
# Please check your internet connection and try again.
```

### convert_exception

Use this function to convert generic exceptions to GAC-specific ones:

```python
from gac.errors import convert_exception, GitError
import subprocess

try:
    subprocess.run(["git", "status"], check=True)
except subprocess.CalledProcessError as e:
    # Convert to a GAC-specific error
    git_error = convert_exception(e, GitError, f"Git error: {e}")
    raise git_error
```

## Best Practices

1. **Use Specific Error Types**
   Always use the most specific error type available that matches the error condition.

2. **Include Actionable Information**
   When raising errors, include enough information for the user to understand and fix the issue.

   ```python
   # Good
   raise ConfigError("API key not found. Set the ANTHROPIC_API_KEY environment variable.")
   
   # Less helpful
   raise ConfigError("Missing API key")
   ```

3. **Convert External Exceptions**
   When catching exceptions from external libraries, convert them to appropriate GAC error types:

   ```python
   try:
       import requests
       response = requests.get(api_url)
       response.raise_for_status()
   except requests.ConnectionError as e:
       raise AIConnectionError(f"Failed to connect to AI provider: {e}")
   except requests.Timeout as e:
       raise AITimeoutError(f"AI provider request timed out: {e}")
   ```

4. **Centralize Error Handling in CLI Functions**
   In CLI entry points, catch and handle all exceptions:

   ```python
   def cli_function():
       try:
           # Main logic here
           result = process_command()
           return result
       except Exception as e:
           handle_error(e)
   ```

5. **Log Before Raising**
   Log detailed information before raising errors to help with debugging:

   ```python
   import logging
   logger = logging.getLogger(__name__)
   
   def some_function():
       try:
           # Logic that might fail
       except Exception as e:
           logger.error(f"Detailed error info: {e}", exc_info=True)
           raise GitError(f"Failed to perform git operation: {e}")
   ```

## Common Error Scenarios

### Configuration Errors

```python
from gac.errors import ConfigError

if not os.environ.get("OPENAI_API_KEY"):
    raise ConfigError(
        "OpenAI API key not found. Set the OPENAI_API_KEY environment variable."
    )
```

### API Errors

```python
from gac.errors import AIConnectionError, AIAuthenticationError, AIRateLimitError

# Connection error
if response.status_code == 503:
    raise AIConnectionError("Service unavailable. The AI provider may be down.")

# Authentication error
if response.status_code == 401:
    raise AIAuthenticationError("Invalid API key or authentication failed.")

# Rate limit error
if response.status_code == 429:
    raise AIRateLimitError("Rate limit exceeded. Please try again later.")
```

### Git Errors

```python
from gac.errors import GitError

try:
    run_subprocess(["git", "status"])
except subprocess.CalledProcessError:
    raise GitError("Git command failed. Make sure you're in a git repository.")
```

## Migrating from Legacy Error Handling

When updating existing code to use the new error system:

1. Replace direct usage of generic exceptions with GAC-specific error types
2. Replace direct sys.exit() calls with handle_error()
3. Replace custom error formatting with format_error_for_user()

Before:

```python
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
```

After:

```python
except Exception as e:
    gac_error = convert_exception(e, GACError)
    handle_error(gac_error)
```
