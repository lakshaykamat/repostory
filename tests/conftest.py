"""Shared fixtures for the repostory test suite."""

from __future__ import annotations

from datetime import datetime

import pytest

from repostory.git_io import Commit, FileChange


def _make(
    sha: str,
    author: str,
    when: str,
    subject: str,
    files: list[tuple[str, int, int]] | None = None,
) -> Commit:
    dt = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
    file_objs = [FileChange(p, a, d) for p, a, d in (files or [])]
    commit = Commit(
        sha=sha,
        author=author,
        subject=subject,
        day=dt.weekday(),
        hour=dt.hour,
        date=dt.strftime("%Y-%m-%d"),
        week=dt.strftime("%G-W%V"),
        month=dt.strftime("%Y-%m"),
        files=file_objs,
        added=sum(f.added for f in file_objs),
        deleted=sum(f.deleted for f in file_objs),
    )
    return commit


@pytest.fixture
def sample_commits() -> list[Commit]:
    """Six commits across two authors with file stats."""
    return [
        _make("a1", "alice@x.com", "2025-01-06 10:00:00", "feat: add login",
              [("src/auth.py", 50, 0), ("src/main.py", 5, 1)]),
        _make("a2", "alice@x.com", "2025-01-06 14:00:00", "fix: handle empty user",
              [("src/auth.py", 8, 2)]),
        _make("b1", "bob@x.com",   "2025-01-07 23:30:00", "docs: README touch-ups",
              [("README.md", 12, 3)]),
        _make("a3", "alice@x.com", "2025-01-13 09:00:00", "refactor: split helpers",
              [("src/auth.py", 30, 25), ("src/helpers.py", 60, 0)]),
        _make("b2", "bob@x.com",   "2025-01-18 02:00:00", "fix typo",
              [("README.md", 1, 1)]),
        _make("a4", "alice@x.com", "2025-02-03 11:00:00", "feat(api): pagination",
              [("src/api.py", 80, 0), ("src/auth.py", 2, 0)]),
    ]


@pytest.fixture
def sample_tags() -> list[dict[str, str]]:
    return [
        {"name": "v0.1.0", "date": "2025-01-10"},
        {"name": "v0.2.0", "date": "2025-01-20"},
        {"name": "v0.3.0", "date": "2025-02-15"},
        {"name": "v0.4.0", "date": "2025-03-01"},
        {"name": "v0.5.0", "date": "2025-03-04"},
    ]
