#!/usr/bin/env python3
"""Token management module for handling token counting and text processing."""

import logging
import re
from typing import Dict, List

from gac.ai_utils import count_tokens

logger = logging.getLogger(__name__)


class TokenManager:
    """Centralized management of token counting and text manipulation."""

    def __init__(self):
        """Initialize the TokenManager."""
        # Priority levels for different parts of a git diff when truncating
        self.diff_priorities = {
            "header": 1,  # Diff headers
            "hunk": 2,  # Hunk headers (@@ -1,5 +1,5 @@)
            "context": 3,  # Context lines
            "addition": 0,  # Added lines (highest priority to keep)
            "deletion": 0,  # Deleted lines (highest priority to keep)
        }

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for
            model: The model name to use for counting

        Returns:
            The number of tokens in the text
        """
        return count_tokens(text, model)

    def truncate_to_token_limit(
        self, text: str, model: str, max_tokens: int, buffer: int = 100
    ) -> str:
        """
        Truncate text to fit within a token limit.

        Args:
            text: The text to truncate
            model: The model name to use for counting
            max_tokens: Maximum number of tokens allowed
            buffer: Token buffer to leave room for other content

        Returns:
            Truncated text that fits within the token limit
        """
        current_tokens = self.count_tokens(text, model)
        target_tokens = max_tokens - buffer

        if current_tokens <= target_tokens:
            return text

        # Simple truncation for short text
        if len(text) < 1000:
            ratio = target_tokens / current_tokens
            return text[: int(len(text) * ratio)]

        # For larger text, use smart truncation
        return self.smart_truncate_text(text, model, target_tokens)

    def smart_truncate_text(self, text: str, model: str, max_tokens: int) -> str:
        """
        Intelligently truncate text to fit within a token limit.

        Args:
            text: The text to truncate
            model: The model name to use for counting
            max_tokens: Maximum number of tokens allowed

        Returns:
            Intelligently truncated text
        """
        if "\n" not in text:
            # No line breaks, simple truncation
            ratio = max_tokens / self.count_tokens(text, model)
            truncated_len = int(len(text) * ratio)
            return text[:truncated_len]

        # Split into lines for more intelligent truncation
        lines = text.split("\n")

        # If it's a git diff, use specialized diff truncation
        if text.startswith("diff --git "):
            return self.smart_truncate_diff(text, model, max_tokens)

        # For other multi-line text, prioritize beginning and end
        return self._truncate_with_beginning_and_end(lines, model, max_tokens)

    def smart_truncate_diff(self, diff: str, model: str, max_tokens: int) -> str:
        """
        Intelligently truncate a git diff to fit within a token limit.

        Args:
            diff: The git diff to truncate
            model: The model name to use for counting
            max_tokens: Maximum number of tokens allowed

        Returns:
            Truncated diff that preserves the most important changes
        """
        # Parse the diff into separate file diffs
        file_diffs = self._split_into_file_diffs(diff)

        # If already within token limit, return unchanged
        if self.count_tokens("\n".join(file_diffs), model) <= max_tokens:
            return diff

        # Calculate tokens per file diff
        file_diff_tokens = {}
        for file_diff in file_diffs:
            file_diff_tokens[file_diff] = self.count_tokens(file_diff, model)

        # Sort file diffs by change density (changes per token)
        file_diffs_sorted = self._sort_diffs_by_importance(file_diffs, file_diff_tokens)

        # Rebuild diff with the most important files first, up to token limit
        result_diff = []
        current_tokens = 0

        for file_diff in file_diffs_sorted:
            tokens = file_diff_tokens[file_diff]

            # If adding this file would exceed limit, try to truncate the file diff
            if current_tokens + tokens > max_tokens:
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 100:  # Only truncate if we have reasonable space
                    truncated_file_diff = self._truncate_file_diff(
                        file_diff, model, remaining_tokens
                    )
                    result_diff.append(truncated_file_diff)
                break

            result_diff.append(file_diff)
            current_tokens += tokens

        # Return reconstructed diff
        result = "\n".join(result_diff)

        # Add indicator that diff was truncated if needed
        if len(result_diff) < len(file_diffs):
            trunc_msg = (f"\n\n[... {len(file_diffs) - len(result_diff)} more files not shown "
                         "due to token limit ...]")
            result += trunc_msg

        return result

    def _truncate_with_beginning_and_end(
        self, lines: List[str], model: str, max_tokens: int
    ) -> str:
        """
        Truncate text by preserving beginning and end.

        Args:
            lines: List of text lines
            model: Model name for token counting
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated text with beginning and end preserved
        """
        if not lines:
            return ""

        # Start with first and last lines
        result = [lines[0]]
        if len(lines) > 1:
            result.append(lines[-1])

        # If already within limit, return original text
        if self.count_tokens("\n".join(result), model) >= max_tokens:
            # Even first and last lines exceed limit, just take the first line
            return lines[0]

        # Add lines from beginning and end until we reach the limit
        beginning_idx = 1
        ending_idx = len(lines) - 2

        # Alternate between adding from beginning and end
        while beginning_idx <= ending_idx:
            # Try adding a line from the beginning
            candidate = lines[beginning_idx]
            if self.count_tokens("\n".join(result + [candidate]), model) < max_tokens:
                result.insert(1, candidate)
                beginning_idx += 1
            else:
                break

            if beginning_idx > ending_idx:
                break

            # Try adding a line from the end
            candidate = lines[ending_idx]
            if self.count_tokens("\n".join(result + [candidate]), model) < max_tokens:
                result.insert(-1, candidate)
                ending_idx -= 1
            else:
                break

        # Add ellipsis in the middle if we truncated
        if beginning_idx <= ending_idx:
            result.insert(len(result) // 2, "...\n...")

        return "\n".join(result)

    def _split_into_file_diffs(self, diff: str) -> List[str]:
        """
        Split a git diff into separate file diffs.

        Args:
            diff: Full git diff

        Returns:
            List of individual file diffs
        """
        if not diff:
            return []

        # Find file diff boundaries
        file_boundaries = []
        lines = diff.split("\n")

        for i, line in enumerate(lines):
            if line.startswith("diff --git "):
                file_boundaries.append(i)

        # Extract each file diff
        file_diffs = []
        for i in range(len(file_boundaries)):
            start = file_boundaries[i]
            end = file_boundaries[i + 1] if i + 1 < len(file_boundaries) else len(lines)
            file_diff = "\n".join(lines[start:end])
            file_diffs.append(file_diff)

        return file_diffs

    def _sort_diffs_by_importance(
        self, file_diffs: List[str], file_diff_tokens: Dict[str, int]
    ) -> List[str]:
        """
        Sort file diffs by their importance (changes per token).

        Args:
            file_diffs: List of file diffs
            file_diff_tokens: Map of file diffs to token counts

        Returns:
            Sorted list of file diffs
        """
        # Calculate importance metrics
        importance_metrics = {}

        for file_diff in file_diffs:
            # Count additions and deletions
            additions = len(re.findall(r"^\+[^\+]", file_diff, re.MULTILINE))
            deletions = len(re.findall(r"^-[^-]", file_diff, re.MULTILINE))

            # Calculate changes per token
            tokens = file_diff_tokens[file_diff]
            changes = additions + deletions

            # Avoid division by zero
            if tokens == 0:
                importance = 0
            else:
                importance = changes / tokens

            importance_metrics[file_diff] = importance

        # Sort by importance (higher first)
        return sorted(file_diffs, key=lambda d: importance_metrics[d], reverse=True)

    def _truncate_file_diff(self, file_diff: str, model: str, max_tokens: int) -> str:
        """
        Truncate a single file diff to fit within token limit.

        Args:
            file_diff: Individual file diff to truncate
            model: Model name for token counting
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated file diff
        """
        lines = file_diff.split("\n")

        # Always keep the header lines
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("@@"):
                header_end = i
                break

        if (
            header_end == 0
            or self.count_tokens("\n".join(lines[: header_end + 1]), model) > max_tokens
        ):
            # Can't even fit the header, just return as much as we can
            result = []
            current_tokens = 0

            for line in lines:
                line_tokens = self.count_tokens(line, model)
                if current_tokens + line_tokens <= max_tokens:
                    result.append(line)
                    current_tokens += line_tokens
                else:
                    break

            return "\n".join(result)

        # Start with the header
        result = lines[: header_end + 1]
        current_tokens = self.count_tokens("\n".join(result), model)

        # Prioritize lines for inclusion
        line_priorities = []

        for i in range(header_end + 1, len(lines)):
            line = lines[i]

            if not line.strip():
                # Skip blank lines
                continue

            # Determine line type and priority
            if line.startswith("+"):
                priority = self.diff_priorities["addition"]
            elif line.startswith("-"):
                priority = self.diff_priorities["deletion"]
            elif line.startswith("@@"):
                priority = self.diff_priorities["hunk"]
            else:
                priority = self.diff_priorities["context"]

            line_priorities.append((i, priority, line))

        # Sort by priority (lower number = higher priority)
        line_priorities.sort(key=lambda x: x[1])

        # Add lines in priority order until we hit the token limit
        for _, _, line in line_priorities:
            line_tokens = self.count_tokens(line, model)

            if current_tokens + line_tokens <= max_tokens:
                result.append(line)
                current_tokens += line_tokens

        # Sort result back into original order to maintain diff readability
        result = sorted(result, key=lambda x: lines.index(x) if x in lines else 0)

        # Add an indicator that the diff was truncated
        if len(result) < len(lines):
            result.append("[... truncated due to token limit ...]")

        return "\n".join(result)
