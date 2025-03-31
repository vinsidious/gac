#!/usr/bin/env python
"""Test script for the Spinner class with message updates."""

import time

from gac.utils import Spinner


def main():
    """Test the spinner with message updates."""
    print("Testing spinner with message updates:")
    with Spinner("Initial message") as spinner:
        time.sleep(2)
        spinner.update_message("Updated message")
        time.sleep(2)
        spinner.update_message("Final message")
        time.sleep(2)
    print("Spinner test completed")


if __name__ == "__main__":
    main()
