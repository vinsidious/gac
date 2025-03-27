"""
Pytest configuration file with coverage setup to avoid the module-not-measured warning.
"""

import os
import sys

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
