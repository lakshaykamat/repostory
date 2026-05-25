"""Smoke test for the HTML report builder."""

from __future__ import annotations

from repostory.aggregator import agg, per_author
from repostory.git_io import Commit
from repostory.report import build_html


def test_build_html_substitutes_payload(sample_commits: list[Commit]) -> None:
    html = build_html(
        all_data=agg(sample_commits),
        author_data=per_author(sample_commits),
        tags=[],
        repo="sample",
        date_range="2025-01-06 – 2025-02-03",
        total_commits=len(sample_commits),
    )
    assert "<!DOCTYPE html>" in html
    assert "{{DATA}}" not in html
    assert "{{STYLES}}" not in html
    assert "{{SCRIPT}}" not in html
    assert "sample" in html
    # Inline JSON payload should mention authors
    assert "alice@x.com" in html
