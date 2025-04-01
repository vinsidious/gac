"""Test module for gac.utils."""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from gac.utils import run_subprocess


class TestUtils(unittest.TestCase):
    """Tests for utility functions."""

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_success(self, mock_run):
        """Test run_subprocess when command succeeds."""
        # Mock subprocess.run to return a success result
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Command output"
        mock_run.return_value = mock_process

        # Call run_subprocess
        result = run_subprocess(["git", "status"])

        # Assert mock was called with the expected arguments
        mock_run.assert_called_once_with(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60,
        )

        # Assert result matches mock stdout
        self.assertEqual(result, "Command output")

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_empty_output(self, mock_run):
        """Test run_subprocess when command succeeds with empty output."""
        # Mock subprocess.run to return a success result with empty output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        # Call run_subprocess
        result = run_subprocess(["git", "status"])

        # Assert result is empty string
        self.assertEqual(result, "")

    @patch("gac.utils.subprocess.run")
    def test_run_subprocess_failure(self, mock_run):
        """Test run_subprocess when command fails."""
        # Mock subprocess.run to raise CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "invalid"], "Output", "Error"
        )

        # Call run_subprocess and expect exception
        with self.assertRaises(subprocess.CalledProcessError):
            run_subprocess(["git", "invalid"])

    def test_run_subprocess_test_mode(self):
        """Test run_subprocess in test mode prevents real git commands."""
        import os

        # Explicitly disable preserve mock to test the test mode functionality
        old_preserve = os.environ.get("_TESTING_PRESERVE_MOCK")
        os.environ.pop("_TESTING_PRESERVE_MOCK", None)

        try:
            # Test that git commands return simulated responses in test mode
            result = run_subprocess(["git", "status"], test_mode=True)
            self.assertIn("M src/gac/utils.py", result)
            self.assertTrue(isinstance(result, str))

            # Test add command
            result = run_subprocess(["git", "add", "file1.py", "file2.py"], test_mode=True)
            self.assertIn("Simulated adding files: file1.py file2.py", result)

            # Test commit command
            result = run_subprocess(["git", "commit", "-m", "Test commit"], test_mode=True)
            self.assertEqual("Simulated commit", result)

            # Test push command with test_mode explicitly set to True
            result = run_subprocess(["git", "push"], test_mode=True)
            self.assertEqual("Simulated push", result)
        finally:
            if old_preserve:
                os.environ["_TESTING_PRESERVE_MOCK"] = old_preserve


if __name__ == "__main__":
    unittest.main()
