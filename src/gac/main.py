"""Main entry point for the GAC application.

This is a backwards compatibility module that imports from cli.py.
All new code should use cli.py directly.
"""

from gac.cli import cli as main

if __name__ == "__main__":
    main()
