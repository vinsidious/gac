#!/usr/bin/env python3
"""Security utilities for detecting secrets and API keys in git diffs.

This module provides functions to scan staged changes for potential secrets,
API keys, and other sensitive information that should not be committed.
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DetectedSecret:
    """Represents a detected secret in a file."""

    file_path: str
    line_number: int | None
    secret_type: str
    matched_text: str
    context: str | None = None


class SecretPatterns:
    """Regex patterns for detecting various types of secrets and API keys."""

    # AWS Access Keys
    AWS_ACCESS_KEY_ID = re.compile(r"(?:AWS_ACCESS_KEY_ID|aws_access_key_id)[\s:=\"']+([A-Z0-9]{20})", re.IGNORECASE)
    AWS_SECRET_ACCESS_KEY = re.compile(
        r"(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)[\s:=\"']+([A-Za-z0-9/+=]{40})", re.IGNORECASE
    )
    AWS_SESSION_TOKEN = re.compile(r"(?:AWS_SESSION_TOKEN|aws_session_token)[\s:=\"']+([A-Za-z0-9/+=]+)", re.IGNORECASE)

    # Generic API Keys
    GENERIC_API_KEY = re.compile(
        r"(?:api[-_]?key|apikey|api[-_]?secret|key)[\s:=\"']+([A-Za-z0-9_\-]{20,})", re.IGNORECASE
    )

    # GitHub Tokens
    GITHUB_TOKEN = re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}")

    # OpenAI API Keys
    OPENAI_API_KEY = re.compile(r"sk-[A-Za-z0-9]{20,}")

    # Anthropic API Keys
    ANTHROPIC_API_KEY = re.compile(r"sk-ant-[A-Za-z0-9\-_]{95,}")

    # Stripe Keys
    STRIPE_KEY = re.compile(r"(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{24,}")

    # Private Keys (PEM format)
    PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")

    # Bearer Tokens
    BEARER_TOKEN = re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)

    # JWT Tokens
    JWT_TOKEN = re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")

    # Database URLs with credentials
    DATABASE_URL = re.compile(
        r"(?:postgresql|mysql|mongodb|redis)://[A-Za-z0-9_-]+:[A-Za-z0-9_@!#$%^&*()+-=]+@[A-Za-z0-9.-]+",
        re.IGNORECASE,
    )

    # SSH Private Keys
    SSH_PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----")

    # Slack Tokens
    SLACK_TOKEN = re.compile(r"xox[baprs]-[A-Za-z0-9-]+")

    # Google API Keys
    GOOGLE_API_KEY = re.compile(r"AIza[0-9A-Za-z_-]{35}")

    # Twilio API Keys
    TWILIO_API_KEY = re.compile(r"SK[a-f0-9]{32}")

    # Generic Password Fields
    PASSWORD = re.compile(r"(?:password|passwd|pwd)[\s:=\"']+([^\s\"']{8,})", re.IGNORECASE)

    # Excluded patterns (common false positives)
    EXCLUDED_PATTERNS = [
        re.compile(r"(?:example|sample|dummy|placeholder|your[-_]?api[-_]?key)", re.IGNORECASE),
        re.compile(r"(?:xxx+|yyy+|zzz+)", re.IGNORECASE),
        re.compile(r"\b(?:123456|password|changeme|secret)\b", re.IGNORECASE),  # Word boundaries
        re.compile(r"ghp_[a-f0-9]{16}", re.IGNORECASE),  # Short GitHub tokens (examples)
        re.compile(r"sk-[a-f0-9]{16}", re.IGNORECASE),  # Short OpenAI keys (examples)
    ]

    @classmethod
    def get_all_patterns(cls) -> dict[str, re.Pattern]:
        """Get all secret detection patterns.

        Returns:
            Dictionary mapping pattern names to compiled regex patterns
        """
        patterns = {}
        for name, value in vars(cls).items():
            if isinstance(value, re.Pattern) and not name.startswith("EXCLUDED"):
                # Convert pattern name to human-readable format
                readable_name = name.replace("_", " ").title()
                patterns[readable_name] = value
        return patterns


def is_false_positive(matched_text: str) -> bool:
    """Check if a matched secret is likely a false positive.

    Args:
        matched_text: The text that matched a secret pattern

    Returns:
        True if the match is likely a false positive
    """
    # Check against excluded patterns
    for pattern in SecretPatterns.EXCLUDED_PATTERNS:
        if pattern.search(matched_text):
            return True

    # Check for all-same characters (e.g., "xxxxxxxxxxxxxxxx")
    if len(set(matched_text.lower())) <= 3 and len(matched_text) > 10:
        return True

    return False


def extract_file_path_from_diff_section(section: str) -> str | None:
    """Extract the file path from a git diff section.

    Args:
        section: A git diff section

    Returns:
        The file path or None if not found
    """
    match = re.search(r"diff --git a/(.*?) b/", section)
    if match:
        return match.group(1)
    return None


def extract_line_number_from_hunk(line: str, hunk_header: str | None) -> int | None:
    """Extract the line number from a diff hunk.

    Args:
        line: The diff line containing the secret
        hunk_header: The most recent hunk header (e.g., "@@ -1,4 +1,5 @@")

    Returns:
        The line number or None if not determinable
    """
    if not hunk_header:
        return None

    # Parse hunk header to get starting line number: @@ -old_start,old_count +new_start,new_count @@
    match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)", hunk_header)
    if not match:
        return None

    return int(match.group(1))


def scan_diff_section(section: str) -> list[DetectedSecret]:
    """Scan a single git diff section for secrets.

    Args:
        section: A git diff section to scan

    Returns:
        List of detected secrets
    """
    secrets = []
    file_path = extract_file_path_from_diff_section(section)

    if not file_path:
        return secrets

    patterns = SecretPatterns.get_all_patterns()
    lines = section.split("\n")
    line_counter = 0

    for line in lines:
        # Track hunk headers for line number extraction
        if line.startswith("@@"):
            # Reset line counter based on hunk header
            match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            if match:
                line_counter = int(match.group(1))
            continue

        # Only scan added lines (starting with '+')
        if not line.startswith("+") or line.startswith("+++"):
            continue

        # Increment line counter for added lines
        line_counter += 1

        # Remove the '+' prefix for pattern matching
        content = line[1:]

        # Check each pattern
        for pattern_name, pattern in patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                matched_text = match.group(0)

                # Skip false positives
                if is_false_positive(matched_text):
                    logger.debug(f"Skipping false positive: {matched_text}")
                    continue

                # Truncate matched text for display (avoid showing full secrets)
                display_text = matched_text[:50] + "..." if len(matched_text) > 50 else matched_text

                secrets.append(
                    DetectedSecret(
                        file_path=file_path,
                        line_number=line_counter,
                        secret_type=pattern_name,
                        matched_text=display_text,
                        context=content.strip(),
                    )
                )

    return secrets


def scan_staged_diff(diff: str) -> list[DetectedSecret]:
    """Scan staged git diff for secrets and API keys.

    Args:
        diff: The staged git diff to scan

    Returns:
        List of detected secrets
    """
    if not diff:
        return []

    # Split diff into sections (one per file)
    sections = re.split(r"(?=diff --git )", diff)
    all_secrets = []

    for section in sections:
        if not section.strip():
            continue

        secrets = scan_diff_section(section)
        all_secrets.extend(secrets)

    logger.info(f"Secret scan complete: found {len(all_secrets)} potential secrets")
    return all_secrets


def get_affected_files(secrets: list[DetectedSecret]) -> list[str]:
    """Get unique list of files containing detected secrets.

    Args:
        secrets: List of detected secrets

    Returns:
        Sorted list of unique file paths
    """
    files = {secret.file_path for secret in secrets}
    return sorted(files)
