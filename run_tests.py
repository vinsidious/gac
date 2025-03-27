#!/usr/bin/env python
"""
Run tests with coverage properly configured to avoid the module-not-measured warning.
"""
import sys

import coverage
import pytest

if __name__ == "__main__":
    # Start coverage before any imports
    cov = coverage.Coverage(source=["gac"], branch=True)
    cov.start()

    # Run pytest
    exit_code = pytest.main(sys.argv[1:])

    # Stop coverage and report
    cov.stop()
    cov.report(show_missing=True)

    sys.exit(exit_code)
