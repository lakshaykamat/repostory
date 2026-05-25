"""Command-line entry point for repostory."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .aggregator import agg, per_author
from .git_io import (
    GitError,
    ensure_git_available,
    ensure_git_repo,
    fetch_remotes,
    get_commits,
    get_tags,
    ref_summary,
    repo_name,
)
from .report import build_html

logger = logging.getLogger("repostory")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="repostory",
        description="Generate a self-contained HTML commit analytics dashboard.",
    )
    p.add_argument("--repo", default=".", help="Path to git repo (default: cwd)")
    p.add_argument(
        "--output",
        default="repostory.html",
        help="Output HTML file (default: repostory.html)",
    )
    p.add_argument("--author", default=None, help="Filter to author email substring")
    p.add_argument(
        "--fetch",
        action="store_true",
        help="Run `git fetch --all --prune` before reading",
    )
    p.add_argument(
        "--fast",
        action="store_true",
        help="Skip --numstat (no file analysis, bus factor, size dist, hotspots)",
    )
    p.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose (DEBUG) logging"
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="Only show warnings and errors"
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def _configure_logging(verbose: bool, quiet: bool) -> None:
    if verbose and quiet:
        raise SystemExit("--verbose and --quiet are mutually exclusive")
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stderr,
    )


def _log_ref_summary(repo_path: Path) -> None:
    refs = ref_summary(repo_path)
    local, remote = refs["local"], refs["remote"]

    def _fmt(items: list[str]) -> str:
        head = ", ".join(items[:5])
        return f"{head}{'...' if len(items) > 5 else ''}"

    logger.info("  local  branches : %d  (%s)", len(local), _fmt(local))
    logger.info("  remote tracking : %d  (%s)", len(remote), _fmt(remote))
    logger.info("  scope           : all of the above, SHA-deduplicated")


def run(args: argparse.Namespace) -> int:
    """Pure entry point — returns exit code."""
    try:
        ensure_git_available()
    except GitError as exc:
        logger.error("error: %s", exc)
        return 2

    repo_path = Path(args.repo).resolve()
    try:
        ensure_git_repo(repo_path)
    except GitError as exc:
        logger.error("error: %s", exc)
        return 2

    if args.fetch:
        logger.info("Fetching from all remotes...")
        ok, msg = fetch_remotes(repo_path)
        logger.info("  %s: %s", "ok" if ok else "warn", msg)
    else:
        logger.info("Tip: pass --fetch to sync remote-tracking refs first.")

    logger.info("\nRef scope:")
    _log_ref_summary(repo_path)

    mode = "fast (no file analysis)" if args.fast else "full (with --numstat)"
    logger.info("\nReading git log [%s]...", mode)
    try:
        commits = get_commits(repo_path, args.author, fast=args.fast)
    except GitError as exc:
        logger.error("error: %s", exc)
        return 1

    if not commits:
        logger.error("No commits found.")
        return 1

    tags = get_tags(repo_path)
    authors_count = len({c.author for c in commits})
    logger.info(
        "Found %s commits · %d author(s) · %d tag(s).",
        f"{len(commits):,}",
        authors_count,
        len(tags),
    )

    logger.info("Aggregating...")
    all_data = agg(commits)
    author_data = per_author(commits)

    dates = sorted({c.date for c in commits})
    date_range = f"{dates[0]} – {dates[-1]}" if len(dates) > 1 else dates[0]

    html = build_html(
        all_data, author_data, tags, repo_name(repo_path), date_range, len(commits)
    )

    out = Path(args.output).resolve()
    out.write_text(html, encoding="utf-8")
    logger.info("Done → %s", out)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose, args.quiet)
    try:
        return run(args)
    except KeyboardInterrupt:
        logger.error("Interrupted")
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
