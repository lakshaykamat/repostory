"""Static constants and regex patterns used across the package."""

from __future__ import annotations

import re

DAYS: tuple[str, ...] = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

MONTHS: tuple[str, ...] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

CONV_TYPES: tuple[str, ...] = (
    "feat", "fix", "refactor", "chore", "test",
    "docs", "style", "perf", "ci", "build",
)

REWORK_RE = re.compile(
    r"\b(fix(?:es|ed)?|bug|hotfix|patch|correct|repair|revert|broke|broken|crash|fail)\b",
    re.IGNORECASE,
)

CONV_RE = re.compile(r"^(\w+)(\(.+?\))?!?\s*:", re.IGNORECASE)

NIGHT_HOUR_START = 22
NIGHT_HOUR_END = 4
WEEKEND_START_DAY = 5
