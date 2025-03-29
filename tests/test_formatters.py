"""Tests for gac.formatting.formatters module."""

from unittest.mock import patch

import pytest

from gac.formatting.formatters import format_staged_files, run_black, run_isort


@pytest.fixture
def mock_get_staged_python_files():
    with patch("gac.formatting.formatters.get_existing_staged_python_files") as mock:
        yield mock


@patch("gac.formatting.formatters.run_subprocess")
def test_run_black_success(mock_run_subprocess, mock_get_staged_python_files):
    mock_get_staged_python_files.return_value = ["file1.py", "file2.py"]
    mock_run_subprocess.return_value = None
    result = run_black()
    assert result is True
    mock_run_subprocess.assert_called_once_with(["black", "file1.py", "file2.py"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_black_no_files(mock_run_subprocess, mock_get_staged_python_files):
    mock_get_staged_python_files.return_value = []
    result = run_black()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_subprocess")
def test_run_isort_success(mock_run_subprocess, mock_get_staged_python_files):
    mock_get_staged_python_files.return_value = ["file1.py", "file2.py"]
    mock_run_subprocess.return_value = None
    result = run_isort()
    assert result is True
    mock_run_subprocess.assert_called_once_with(["isort", "file1.py", "file2.py"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_isort_no_files(mock_run_subprocess, mock_get_staged_python_files):
    mock_get_staged_python_files.return_value = []
    result = run_isort()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
def test_format_staged_files_success(mock_run_isort, mock_run_black, mock_get_staged_python_files):
    mock_get_staged_python_files.return_value = ["file1.py", "file2.py"]
    mock_run_black.return_value = True
    mock_run_isort.return_value = True
    result = format_staged_files()
    assert result is True
    mock_run_black.assert_called_once()
    mock_run_isort.assert_called_once()


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
def test_format_staged_files_no_files(mock_run_isort, mock_run_black, mock_get_staged_python_files):
    mock_get_staged_python_files.return_value = []
    result = format_staged_files()
    assert result is False
    mock_run_black.assert_not_called()
    mock_run_isort.assert_not_called()


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
def test_format_staged_files_black_fails(
    mock_run_isort, mock_run_black, mock_get_staged_python_files
):
    mock_get_staged_python_files.return_value = ["file1.py", "file2.py"]
    mock_run_black.return_value = False
    mock_run_isort.return_value = True
    result = format_staged_files()
    assert result is True
    mock_run_black.assert_called_once()
    mock_run_isort.assert_called_once()
