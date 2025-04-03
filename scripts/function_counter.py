#!/usr/bin/env python3
import glob
import os
import re
from collections import Counter


def analyze_python_functions(repo_path):
    """Analyze Python function definitions and calls across a repository."""
    function_def_pattern = re.compile(r"def\s+([a-zA-Z0-9_]+)\s*\(")

    all_defined_functions = {}
    all_file_contents = {}

    all_files = glob.glob(f"{repo_path}/**/*.py", recursive=True)

    for file_path in all_files:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                all_file_contents[file_path] = content

                for func_name in function_def_pattern.findall(content):
                    all_defined_functions[func_name] = file_path
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    total_calls = Counter()

    for file_path, content in all_file_contents.items():
        for func_name in all_defined_functions:
            call_pattern = re.compile(r"(?<![a-zA-Z0-9_])" + re.escape(func_name) + r"\s*\(")
            calls = call_pattern.findall(content)
            total_calls[func_name] += len(calls)

    for func_name in all_defined_functions:
        total_calls[func_name] = max(0, total_calls[func_name] - 1)

    return all_defined_functions, total_calls


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Count Python function calls across a repository")
    parser.add_argument("repo_path", help="Path to the repository")
    parser.add_argument("--max", type=int, help="Maximum function call count to display")
    args = parser.parse_args()

    all_defined_functions, total_calls = analyze_python_functions(args.repo_path)

    print(f"{'Function Name':<30} {'Call Count':<10} {'Defined In'}")
    print("-" * 80)

    for func_name in sorted(all_defined_functions.keys()):
        # Skip functions with call counts greater than max (if specified)
        if args.max is not None and total_calls[func_name] > args.max:
            continue

        rel_path = os.path.relpath(all_defined_functions[func_name], args.repo_path)
        print(f"{func_name:<30} {total_calls[func_name]:<10} {rel_path}")

    print("-" * 80)

    if args.max is not None:
        displayed_count = sum(
            1 for func_name in all_defined_functions if total_calls[func_name] <= args.max
        )
        print(f"Displayed functions: {displayed_count} (call count ≤ {args.max})")
    else:
        print(f"Total functions: {len(all_defined_functions)}")

    print(f"Unused functions: {sum(1 for _, count in total_calls.items() if count == 0)}")


if __name__ == "__main__":
    main()
