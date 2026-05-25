"""Subprocess wrappers around `git` with structured output and error handling."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitError(RuntimeError):
    """Raised when a git invocation fails or returns unparseable output."""


@dataclass
class FileChange:
    path: str
    added: int
    deleted: int

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "added": self.added, "deleted": self.deleted}


@dataclass
class Commit:
    sha: str
    author: str
    subject: str
    day: int
    hour: int
    date: str
    week: str
    month: str
    files: list[FileChange] = field(default_factory=list)
    added: int = 0
    deleted: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "sha": self.sha,
            "author": self.author,
            "subject": self.subject,
            "day": self.day,
            "hour": self.hour,
            "date": self.date,
            "week": self.week,
            "month": self.month,
            "files": [f.as_dict() for f in self.files],
            "added": self.added,
            "deleted": self.deleted,
        }


def ensure_git_available() -> None:
    """Verify the git binary is on PATH; raise GitError otherwise."""
    if shutil.which("git") is None:
        raise GitError("`git` executable not found on PATH")


def ensure_git_repo(repo_path: Path) -> None:
    """Validate that `repo_path` is a git working tree."""
    if not repo_path.is_dir():
        raise GitError(f"{repo_path} is not a directory")
    if not (repo_path / ".git").exists():
        raise GitError(f"{repo_path} is not a git repository (no .git found)")


def _run_git(
    args: list[str],
    repo_path: Path,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run git with utf-8 decoding that tolerates malformed bytes."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result


def fetch_remotes(repo_path: Path) -> tuple[bool, str]:
    """Fetch from all remotes with --prune. Returns (ok, message)."""
    try:
        result = _run_git(["fetch", "--all", "--prune"], repo_path, check=False)
    except FileNotFoundError as exc:
        return False, str(exc)
    if result.returncode != 0:
        return False, result.stderr.strip()
    msg = (result.stdout + result.stderr).strip()
    return True, msg or "already up to date"


def ref_summary(repo_path: Path) -> dict[str, list[str]]:
    """Return local and remote-tracking branch names."""
    local = _run_git(
        ["branch", "--format=%(refname:short)"], repo_path
    ).stdout.strip().splitlines()
    remote = _run_git(
        ["branch", "-r", "--format=%(refname:short)"], repo_path
    ).stdout.strip().splitlines()
    return {"local": local, "remote": remote}


def repo_name(repo_path: Path) -> str:
    """Best-effort short name for the repo (toplevel basename)."""
    try:
        result = _run_git(["rev-parse", "--show-toplevel"], repo_path, check=False)
        top = result.stdout.strip()
        if top:
            return os.path.basename(top)
    except GitError:
        pass
    return os.path.basename(os.path.abspath(repo_path))


def _parse_commit_header(parts: list[str], *, with_marker: bool) -> Commit | None:
    """Parse a tab-separated header line into a Commit (or None on bad input)."""
    offset = 1 if with_marker else 0
    if len(parts) < 3 + offset:
        return None
    sha = parts[offset]
    email = parts[offset + 1].strip()
    ts = parts[offset + 2]
    subject = parts[offset + 3] if len(parts) > 3 + offset else ""
    try:
        dt = datetime.strptime(ts.rsplit(" ", 1)[0], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return Commit(
        sha=sha,
        author=email,
        subject=subject,
        day=dt.weekday(),
        hour=dt.hour,
        date=dt.strftime("%Y-%m-%d"),
        week=dt.strftime("%G-W%V"),
        month=dt.strftime("%Y-%m"),
    )


def _parse_numstat(line: str) -> FileChange | None:
    p = line.split("\t", 2)
    if len(p) != 3:
        return None
    try:
        added = int(p[0]) if p[0] != "-" else 0
        deleted = int(p[1]) if p[1] != "-" else 0
    except ValueError:
        return None
    return FileChange(path=p[2].strip(), added=added, deleted=deleted)


def get_commits(
    repo_path: Path,
    author_filter: str | None = None,
    *,
    fast: bool = False,
) -> list[Commit]:
    """Read deduplicated commits across all refs.

    When `fast` is True, --numstat is skipped (no file-level data).
    """
    if fast:
        args = ["log", "--all", "--no-merges", "--format=%H\t%ae\t%ai\t%s"]
    else:
        args = [
            "log",
            "--all",
            "--no-merges",
            "--format=COMMIT\t%H\t%ae\t%ai\t%s",
            "--numstat",
        ]
    if author_filter:
        args.append(f"--author={author_filter}")

    result = _run_git(args, repo_path)
    seen: set[str] = set()
    commits: list[Commit] = []

    if fast:
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("\t", 3)
            commit = _parse_commit_header(parts, with_marker=False)
            if commit is None or commit.sha in seen:
                continue
            seen.add(commit.sha)
            commits.append(commit)
        return commits

    current: Commit | None = None
    for line in result.stdout.strip().splitlines():
        if line.startswith("COMMIT\t"):
            if current is not None and current.sha not in seen:
                seen.add(current.sha)
                commits.append(current)
            current = _parse_commit_header(line.split("\t", 4), with_marker=True)
        elif line.strip() and current is not None:
            fc = _parse_numstat(line)
            if fc is not None:
                current.files.append(fc)
                current.added += fc.added
                current.deleted += fc.deleted
    if current is not None and current.sha not in seen:
        commits.append(current)
    return commits


def get_tags(repo_path: Path) -> list[dict[str, str]]:
    """Return tags with ISO creation dates, oldest first."""
    result = _run_git(
        [
            "tag",
            "-l",
            "--sort=creatordate",
            "--format=%(refname:short)\t%(creatordate:iso)",
        ],
        repo_path,
    )
    tags: list[dict[str, str]] = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        name, ts = parts
        try:
            dt = datetime.strptime(ts.rsplit(" ", 1)[0].strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.debug("Skipping tag %s — unparseable date %r", name, ts)
            continue
        tags.append({"name": name, "date": dt.strftime("%Y-%m-%d")})
    return tags
