"""Command-line entry point for repostory."""

from __future__ import annotations

import argparse
import logging
import sys
import time
import webbrowser
from pathlib import Path

from . import __version__
from ._ui import bold, cyan, dim, fmt_ms, fmt_size, green, plural, red, yellow
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
        "--no-open",
        action="store_true",
        help="Do not auto-open the report in a browser",
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
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)


def _log_refs(repo_path: Path) -> None:
    refs = ref_summary(repo_path)
    local, remote = refs["local"], refs["remote"]

    def _fmt(items: list[str]) -> str:
        head = ", ".join(items[:5])
        return f"{head}{'...' if len(items) > 5 else ''}"

    logger.info("")
    logger.info(bold("Refs"))
    logger.info("  local   %3d  %s", len(local), dim(_fmt(local)) or dim("—"))
    logger.info("  remote  %3d  %s", len(remote), dim(_fmt(remote)) or dim("—"))
    logger.info("  scope        %s", dim("SHA-deduplicated union"))


def _step(label: str, elapsed: float) -> None:
    logger.info("  %s %-38s %s", cyan("→"), label, dim(fmt_ms(elapsed).rjust(8)))


def _error(exc: BaseException) -> None:
    logger.error("%s %s", red("error:"), exc)


def run(args: argparse.Namespace) -> int:
    """Pure entry point — returns exit code."""
    total_start = time.perf_counter()

    try:
        ensure_git_available()
    except GitError as exc:
        _error(exc)
        return 2

    repo_path = Path(args.repo).resolve()
    try:
        ensure_git_repo(repo_path)
    except GitError as exc:
        _error(exc)
        return 2

    logger.info(
        "%s %s  %s",
        bold("repostory"),
        dim(__version__),
        dim(str(repo_path)),
    )

    if args.fetch:
        t = time.perf_counter()
        ok, msg = fetch_remotes(repo_path)
        _step("fetch remotes", time.perf_counter() - t)
        if not ok:
            logger.warning("  %s %s", yellow("warn:"), msg)
    else:
        logger.info("  %s pass %s to sync remote refs first", dim("tip:"), bold("--fetch"))

    _log_refs(repo_path)

    logger.info("")
    mode = "fast" if args.fast else "full"
    t = time.perf_counter()
    try:
        commits = get_commits(repo_path, args.author, fast=args.fast)
    except GitError as exc:
        _error(exc)
        return 1
    _step(f"reading git log ({mode})", time.perf_counter() - t)

    if not commits:
        _error(Exception("no commits found"))
        return 1

    tags = get_tags(repo_path)
    authors_count = len({c.author for c in commits})
    logger.info(
        "  %s %s · %s · %s",
        dim("·"),
        plural(len(commits), "commit"),
        plural(authors_count, "author"),
        plural(len(tags), "tag"),
    )

    t = time.perf_counter()
    all_data = agg(commits)
    author_data = per_author(commits)
    _step("aggregating", time.perf_counter() - t)

    dates = sorted({c.date for c in commits})
    date_range = f"{dates[0]} – {dates[-1]}" if len(dates) > 1 else dates[0]

    t = time.perf_counter()
    html = build_html(
        all_data, author_data, tags, repo_name(repo_path), date_range, len(commits)
    )
    out = Path(args.output).resolve()
    out.write_text(html, encoding="utf-8")
    _step("writing report", time.perf_counter() - t)

    elapsed = time.perf_counter() - total_start
    size = out.stat().st_size

    logger.info("")
    logger.info("%s in %s", green("Done"), bold(fmt_ms(elapsed)))
    logger.info("  %s %s %s", cyan("→"), out, dim(f"({fmt_size(size)})"))

    if args.no_open:
        return 0

    if webbrowser.open(out.as_uri()):
        logger.info("  %s opened in browser", cyan("→"))
    else:
        logger.info("  %s could not open browser; open the file manually", yellow("!"))

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
