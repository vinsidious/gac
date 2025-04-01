"""
Utility script to find missing files in black formatting command.
"""

import os
import subprocess


def main():
    """Run black with debug output to find missing files."""
    # Files specified in the error message
    files = [
        "src/gac/ai_utils.py",
        "src/gac/cache.py",  # This file no longer exists
        "src/gac/cli.py",
        "src/gac/git.py",
        "src/gac/utils.py",
        "src/gac/workflow.py",
        "tests/test_ai_utils.py",
        "tests/test_cache.py",  # This file no longer exists
        "tests/test_core.py",
        "tests/test_git.py",
        "tests/test_utils.py",
    ]

    print("Checking for existence of files:")
    for file in files:
        exists = os.path.exists(file)
        print(f"  {file}: {'EXISTS' if exists else 'MISSING'}")

    print("\nSearching for possible sources of hardcoded file list...")
    search_paths = ["src", "tests", "scripts"]
    for path in search_paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r") as f:
                        content = f.read()
                        if "cache.py" in content:
                            print(f"Found 'cache.py' in {full_path}")

    print("\nTrying to trace black command execution...")
    try:
        # Run black with verbose output
        cmd = ["black", "--verbose", "src/gac"]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
    except Exception as e:
        print(f"Error running black: {e}")


if __name__ == "__main__":
    main()
