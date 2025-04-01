# SPDX-FileCopyrightText: 2024-present cellwebb <cellwebb@users.noreply.github.com>
#
# SPDX-License-Identifier: MIT
# flake8: noqa: F401

"""Git Auto Commit (GAC) package.

A tool to generate commit messages using AI.
"""

from gac.__about__ import __version__
from gac.ai import generate_commit_message
from gac.core import commit_changes, generate_commit
from gac.format import format_files
from gac.git import commit_changes as git_commit
from gac.git import (
    get_staged_diff,
    get_staged_files,
    get_status,
    push_changes,
    stage_all_files,
    stage_files,
)
from gac.prompt import build_prompt, clean_commit_message

__all__ = [
    "__version__",
    "generate_commit_message",
    "generate_commit",
    "commit_changes",
    "format_files",
    "build_prompt",
    "clean_commit_message",
    "get_staged_diff",
    "get_staged_files",
    "get_status",
    "stage_all_files",
    "stage_files",
    "git_commit",
    "push_changes",
]
