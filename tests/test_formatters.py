"""Tests for gac.formatting.formatters module."""

from unittest.mock import patch

import pytest

from gac.formatting.formatters import (
    format_staged_files,
    run_black,
    run_gofmt,
    run_isort,
    run_prettier,
    run_rustfmt,
)


@pytest.fixture
def mock_get_staged_files():
    with patch("gac.formatting.formatters.get_staged_files") as mock:
        yield mock


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_black_success(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.py", "file2.py"]
    mock_run_subprocess.return_value = None
    result = run_black()
    assert result is True
    mock_run_subprocess.assert_called_once_with(["black", "file1.py", "file2.py"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_black_no_files(mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = []
    result = run_black()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_black_error(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.py", "file2.py"]
    mock_run_subprocess.side_effect = Exception("Command failed")
    result = run_black()
    assert result is False
    mock_run_subprocess.assert_called_once_with(["black", "file1.py", "file2.py"])


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_isort_success(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.py", "file2.py"]
    mock_run_subprocess.return_value = None
    result = run_isort()
    assert result is True
    mock_run_subprocess.assert_called_once_with(["isort", "file1.py", "file2.py"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_isort_no_files(mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = []
    result = run_isort()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_isort_error(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.py", "file2.py"]
    mock_run_subprocess.side_effect = Exception("Command failed")
    result = run_isort()
    assert result is False
    mock_run_subprocess.assert_called_once_with(["isort", "file1.py", "file2.py"])


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_prettier_success(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.js", "file2.tsx"]
    mock_run_subprocess.return_value = None
    result = run_prettier(files=["file1.js", "file2.tsx"])
    assert result is True
    mock_run_subprocess.assert_called_once_with(["prettier", "--write", "file1.js", "file2.tsx"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_prettier_no_files(mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = []
    result = run_prettier()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_prettier_error(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.js", "file2.tsx"]
    mock_run_subprocess.side_effect = Exception("Command failed")
    result = run_prettier(files=["file1.js", "file2.tsx"])
    assert result is False
    mock_run_subprocess.assert_called_once_with(["prettier", "--write", "file1.js", "file2.tsx"])


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_rustfmt_success(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.rs", "file2.rs"]
    mock_run_subprocess.return_value = None
    result = run_rustfmt()
    assert result is True
    mock_run_subprocess.assert_called_once_with(["rustfmt", "file1.rs", "file2.rs"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_rustfmt_no_files(mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = []
    result = run_rustfmt()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_rustfmt_error(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.rs", "file2.rs"]
    mock_run_subprocess.side_effect = Exception("Command failed")
    result = run_rustfmt()
    assert result is False
    mock_run_subprocess.assert_called_once_with(["rustfmt", "file1.rs", "file2.rs"])


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_gofmt_success(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.go", "file2.go"]
    mock_run_subprocess.return_value = None
    result = run_gofmt()
    assert result is True
    mock_run_subprocess.assert_called_once_with(["gofmt", "-w", "file1.go", "file2.go"])


@patch("gac.formatting.formatters.run_subprocess")
def test_run_gofmt_no_files(mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = []
    result = run_gofmt()
    assert result is False
    mock_run_subprocess.assert_not_called()


@patch("gac.formatting.formatters.run_subprocess")
@patch("gac.formatting.formatters.os.path.exists", return_value=True)
def test_run_gofmt_error(mock_exists, mock_run_subprocess, mock_get_staged_files):
    mock_get_staged_files.return_value = ["file1.go", "file2.go"]
    mock_run_subprocess.side_effect = Exception("Command failed")
    result = run_gofmt()
    assert result is False
    mock_run_subprocess.assert_called_once_with(["gofmt", "-w", "file1.go", "file2.go"])


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
@patch("gac.formatting.formatters.run_prettier")
@patch("gac.formatting.formatters.run_rustfmt")
@patch("gac.formatting.formatters.run_gofmt")
def test_format_staged_files_success(
    mock_run_gofmt,
    mock_run_rustfmt,
    mock_run_prettier,
    mock_run_isort,
    mock_run_black,
    mock_get_staged_files,
):
    # Set up mock return values for the new implementation
    mock_get_staged_files.return_value = [
        "file1.py",
        "file2.py",
        "file1.js",
        "file1.rs",
        "file1.go",
    ]

    mock_run_black.return_value = True
    mock_run_isort.return_value = True
    mock_run_prettier.return_value = True
    mock_run_rustfmt.return_value = True
    mock_run_gofmt.return_value = True

    formatted, exts = format_staged_files()

    assert formatted is True
    assert ".py" in exts
    mock_run_black.assert_called_once()
    mock_run_isort.assert_called_once()
    mock_run_prettier.assert_called_once()
    mock_run_rustfmt.assert_called_once()
    mock_run_gofmt.assert_called_once()


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
@patch("gac.formatting.formatters.run_prettier")
@patch("gac.formatting.formatters.run_rustfmt")
@patch("gac.formatting.formatters.run_gofmt")
@patch("gac.formatting.formatters.stage_files")
def test_format_staged_files_with_stage(
    mock_stage_files,
    mock_run_gofmt,
    mock_run_rustfmt,
    mock_run_prettier,
    mock_run_isort,
    mock_run_black,
    mock_get_staged_files,
):
    # Setup staged files for the new implementation
    mock_get_staged_files.return_value = ["file1.py", "file1.js"]

    mock_run_black.return_value = True
    mock_run_isort.return_value = False
    mock_run_prettier.return_value = True
    mock_run_rustfmt.return_value = False
    mock_run_gofmt.return_value = False

    formatted, exts = format_staged_files(stage_after_format=True)

    assert formatted is True
    assert ".py" in exts
    assert ".js" in exts
    mock_stage_files.assert_called_once()


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
@patch("gac.formatting.formatters.run_prettier")
@patch("gac.formatting.formatters.run_rustfmt")
@patch("gac.formatting.formatters.run_gofmt")
def test_format_staged_files_no_files(
    mock_run_gofmt,
    mock_run_rustfmt,
    mock_run_prettier,
    mock_run_isort,
    mock_run_black,
    mock_get_staged_files,
):
    mock_get_staged_files.return_value = []
    formatted, exts = format_staged_files()
    assert formatted is False
    assert len(exts) == 0
    mock_run_black.assert_not_called()
    mock_run_isort.assert_not_called()
    mock_run_prettier.assert_not_called()
    mock_run_rustfmt.assert_not_called()
    mock_run_gofmt.assert_not_called()


@patch("gac.formatting.formatters.run_black")
@patch("gac.formatting.formatters.run_isort")
@patch("gac.formatting.formatters.run_prettier")
@patch("gac.formatting.formatters.run_rustfmt")
@patch("gac.formatting.formatters.run_gofmt")
@patch("gac.formatting.formatters.logger")
def test_format_staged_files_with_failures(
    mock_logger,
    mock_run_gofmt,
    mock_run_rustfmt,
    mock_run_prettier,
    mock_run_isort,
    mock_run_black,
    mock_get_staged_files,
):
    # Setup staged files with various extensions
    mock_get_staged_files.return_value = [
        "file1.py",
        "file2.py",
        "file1.js",
        "file1.rs",
        "file1.go",
        "file1.md",
    ]

    # Setup some formatters to fail, others to succeed
    mock_run_black.return_value = True
    mock_run_isort.return_value = False  # isort fails
    mock_run_prettier.return_value = True
    mock_run_rustfmt.return_value = False  # rustfmt fails

    # Need to use a regular function for the side effect, not an exception
    def gofmt_side_effect(*args, **kwargs):
        return False  # Just return False instead of raising an exception

    mock_run_gofmt.side_effect = gofmt_side_effect

    formatted, exts = format_staged_files()

    # Should still be True as some formatters succeeded
    assert formatted is True

    # Make sure successful formatters added their extensions
    assert ".py" in exts  # black succeeded
    assert ".js" in exts  # prettier succeeded for JS
    assert ".md" in exts  # prettier succeeded for MD

    # Failed formatters should not have added extensions
    assert ".rs" not in exts  # rustfmt failed
    assert ".go" not in exts  # gofmt failed

    # Verify all formatters were called
    mock_run_black.assert_called_once()
    mock_run_isort.assert_called_once()
    mock_run_prettier.assert_called()
    mock_run_rustfmt.assert_called_once()
    mock_run_gofmt.assert_called_once()
