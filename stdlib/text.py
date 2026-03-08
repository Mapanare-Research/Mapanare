"""mapanare.text -- string manipulation utilities."""

from __future__ import annotations

import re
from typing import Sequence

# ---------------------------------------------------------------------------
# Case conversion
# ---------------------------------------------------------------------------


def to_upper(s: str) -> str:
    """Convert string to uppercase."""
    return s.upper()


def to_lower(s: str) -> str:
    """Convert string to lowercase."""
    return s.lower()


def capitalize(s: str) -> str:
    """Capitalize the first character."""
    return s.capitalize()


def title_case(s: str) -> str:
    """Convert to title case (each word capitalized)."""
    return s.title()


def camel_case(s: str) -> str:
    """Convert snake_case or kebab-case to camelCase."""
    parts = re.split(r"[_\-\s]+", s)
    if not parts:
        return s
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def snake_case(s: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    s = re.sub(r"[\-\s]+", "_", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def kebab_case(s: str) -> str:
    """Convert to kebab-case."""
    return snake_case(s).replace("_", "-")


# ---------------------------------------------------------------------------
# Trimming and padding
# ---------------------------------------------------------------------------


def trim(s: str) -> str:
    """Remove leading and trailing whitespace."""
    return s.strip()


def trim_start(s: str) -> str:
    """Remove leading whitespace."""
    return s.lstrip()


def trim_end(s: str) -> str:
    """Remove trailing whitespace."""
    return s.rstrip()


def pad_start(s: str, width: int, fill: str = " ") -> str:
    """Pad string on the left to reach width."""
    if len(fill) != 1:
        raise ValueError("fill must be a single character")
    return s.rjust(width, fill)


def pad_end(s: str, width: int, fill: str = " ") -> str:
    """Pad string on the right to reach width."""
    if len(fill) != 1:
        raise ValueError("fill must be a single character")
    return s.ljust(width, fill)


def center(s: str, width: int, fill: str = " ") -> str:
    """Center string within width."""
    if len(fill) != 1:
        raise ValueError("fill must be a single character")
    return s.center(width, fill)


# ---------------------------------------------------------------------------
# Search and replace
# ---------------------------------------------------------------------------


def contains(s: str, sub: str) -> bool:
    """Check if s contains sub."""
    return sub in s


def starts_with(s: str, prefix: str) -> bool:
    """Check if s starts with prefix."""
    return s.startswith(prefix)


def ends_with(s: str, suffix: str) -> bool:
    """Check if s ends with suffix."""
    return s.endswith(suffix)


def index_of(s: str, sub: str) -> int:
    """Return index of first occurrence of sub, or -1 if not found."""
    return s.find(sub)


def replace(s: str, old: str, new: str, count: int = -1) -> str:
    """Replace occurrences of old with new."""
    if count < 0:
        return s.replace(old, new)
    return s.replace(old, new, count)


def replace_regex(s: str, pattern: str, replacement: str) -> str:
    """Replace all regex matches."""
    return re.sub(pattern, replacement, s)


# ---------------------------------------------------------------------------
# Splitting and joining
# ---------------------------------------------------------------------------


def split(s: str, sep: str | None = None, max_splits: int = -1) -> list[str]:
    """Split string by separator."""
    if max_splits < 0:
        return s.split(sep)
    return s.split(sep, max_splits)


def join(parts: Sequence[str], sep: str = "") -> str:
    """Join strings with separator."""
    return sep.join(parts)


def lines(s: str) -> list[str]:
    """Split string into lines."""
    return s.splitlines()


def words(s: str) -> list[str]:
    """Split string into words (whitespace-separated)."""
    return s.split()


# ---------------------------------------------------------------------------
# Character utilities
# ---------------------------------------------------------------------------


def char_at(s: str, index: int) -> str:
    """Return character at index."""
    return s[index]


def char_code(c: str) -> int:
    """Return Unicode code point of character."""
    return ord(c)


def from_char_code(code: int) -> str:
    """Return character from Unicode code point."""
    return chr(code)


def is_alpha(s: str) -> bool:
    """Check if string contains only alphabetic characters."""
    return s.isalpha() if s else False


def is_digit(s: str) -> bool:
    """Check if string contains only digits."""
    return s.isdigit() if s else False


def is_alphanumeric(s: str) -> bool:
    """Check if string contains only alphanumeric characters."""
    return s.isalnum() if s else False


def is_whitespace(s: str) -> bool:
    """Check if string contains only whitespace."""
    return s.isspace() if s else False


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


def reverse(s: str) -> str:
    """Reverse a string."""
    return s[::-1]


def repeat(s: str, n: int) -> str:
    """Repeat a string n times."""
    return s * n


def truncate(s: str, max_len: int, suffix: str = "...") -> str:
    """Truncate string to max_len, appending suffix if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def count(s: str, sub: str) -> int:
    """Count non-overlapping occurrences of sub in s."""
    return s.count(sub)


def is_empty(s: str) -> bool:
    """Check if string is empty or only whitespace."""
    return len(s.strip()) == 0


def slug(s: str) -> str:
    """Convert string to URL-friendly slug."""
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")
