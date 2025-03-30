"""
Pytest configuration file with coverage setup to avoid the module-not-measured warning.
"""

import os
import sys
from unittest.mock import patch

import pytest

# Add the src directory to the path to ensure proper importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


# Disable coverage warnings about modules already imported
def pytest_configure(config):
    import warnings

    from coverage.exceptions import CoverageWarning

    warnings.filterwarnings(
        "ignore", category=CoverageWarning, message="Module .* was previously imported"
    )


@pytest.fixture
def mock_run_subprocess():
    """Mock for gac.core.run_subprocess."""
    with patch("gac.core.run_subprocess") as mock:
        yield mock


@pytest.fixture
def mock_get_staged_files():
    """Mock for gac.core.get_staged_files."""
    with patch("gac.core.get_staged_files") as mock:
        mock.return_value = ["file1.py", "file2.txt"]
        yield mock


@pytest.fixture
def mock_get_config():
    """Mock for gac.core.get_config."""
    with patch("gac.core.get_config") as mock:
        mock.return_value = {"model": "anthropic:claude-3-haiku", "use_formatting": True}
        yield mock


@pytest.fixture
def mock_send_to_llm():
    """Mock for gac.core.send_to_llm."""
    with patch("gac.core.send_to_llm") as mock:
        mock.return_value = "Generated commit message"
        yield mock


@pytest.fixture
def mock_commit_changes():
    """Mock for gac.core.commit_changes."""
    with patch("gac.core.commit_changes") as mock:
        yield mock


@pytest.fixture
def mock_prompt():
    """Mock for click.prompt."""
    with patch("click.prompt") as mock:
        mock.return_value = "y"  # Default to "yes"
        yield mock


@pytest.fixture
def mock_print():
    """Mock for builtins.print."""
    with patch("builtins.print") as mock:
        yield mock


@pytest.fixture
def mock_logging():
    """Mock for gac.core.logging."""
    with patch("gac.core.logging") as mock:
        yield mock


@pytest.fixture
def mock_count_tokens():
    """Mock for gac.core.count_tokens."""
    with patch("gac.core.count_tokens") as mock:
        mock.return_value = 100
        yield mock


@pytest.fixture
def mock_build_prompt():
    """Mock for gac.core.build_prompt."""
    with patch("gac.core.build_prompt") as mock:
        mock.return_value = "Test prompt"
        yield mock


@pytest.fixture
def base_mocks(
    mock_print,
    mock_prompt,
    mock_run_subprocess,
    mock_commit_changes,
    mock_send_to_llm,
    mock_get_staged_files,
    mock_get_config,
):
    """Fixture that provides all the common mocks for main() function tests."""
    return {
        "print": mock_print,
        "prompt": mock_prompt,
        "run_subprocess": mock_run_subprocess,
        "commit_changes": mock_commit_changes,
        "send_to_llm": mock_send_to_llm,
        "get_staged_files": mock_get_staged_files,
        "get_config": mock_get_config,
    }
