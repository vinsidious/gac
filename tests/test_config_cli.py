import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from gac.config_cli import config


def test_config_cli_show_set_get_unset(monkeypatch):
    runner = CliRunner()
    # Use a temp file for $HOME/.gac.env
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)

        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.config_cli.GAC_ENV_PATH", fake_path):
            # Test 'set'
            result = runner.invoke(config, ["set", "TEST_KEY", "test_value"])
            assert result.exit_code == 0
            assert "Set TEST_KEY" in result.output
            # Test 'get'
            result = runner.invoke(config, ["get", "TEST_KEY"])
            assert result.exit_code == 0
            assert "test_value" in result.output
            # Test 'show'
            result = runner.invoke(config, ["show"])
            assert result.exit_code == 0
            assert "TEST_KEY='test_value'" in result.output
            # Test 'unset'
            result = runner.invoke(config, ["unset", "TEST_KEY"])
            assert result.exit_code == 0
            assert "Unset TEST_KEY" in result.output
            # Should not find TEST_KEY now
            os.environ.pop("TEST_KEY", None)
            result = runner.invoke(config, ["get", "TEST_KEY"])
            assert result.exit_code == 0
            assert "not set" in result.output


def test_config_show_no_file():
    """Test show command when .gac.env doesn't exist."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.config_cli.GAC_ENV_PATH", fake_path):
            result = runner.invoke(config, ["show"])
            assert result.exit_code == 0
            assert "No $HOME/.gac.env found" in result.output


def test_config_unset_no_file():
    """Test unset command when .gac.env doesn't exist."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".gac.env"
        with patch("gac.config_cli.GAC_ENV_PATH", fake_path):
            result = runner.invoke(config, ["unset", "NONEXISTENT_KEY"])
            assert result.exit_code == 0
            assert "No $HOME/.gac.env found" in result.output


def test_config_get_missing_key(monkeypatch):
    """Test get command for a key that doesn't exist in .gac.env."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)
        # Create empty .gac.env
        result = runner.invoke(config, ["set", "EXISTING_KEY", "value"])
        assert result.exit_code == 0
        # Try to get a non-existent key
        os.environ.pop("MISSING_KEY", None)
        result = runner.invoke(config, ["get", "MISSING_KEY"])
        assert result.exit_code == 0
        assert "not set" in result.output
