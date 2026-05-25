"""Assemble the self-contained HTML report from templates + payload."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

from .cadence import release_cadence
from .constants import DAYS, MONTHS

@lru_cache(maxsize=1)
def _load_template_parts() -> tuple[str, str, str]:
    """Read the HTML shell, CSS, and JS once and cache them."""
    # Access via parent package: templates/ has no __init__.py, and on
    # Python 3.9 resources.files("repostory.templates") treats it as a
    # namespace package and returns a MultiplexedPath that breaks joinpath.
    templates = resources.files("repostory") / "templates"
    html = (templates / "dashboard.html").read_text(encoding="utf-8")
    css = (templates / "styles.css").read_text(encoding="utf-8")
    js = (templates / "dashboard.js").read_text(encoding="utf-8")
    return html, css, js


def build_html(
    all_data: dict[str, Any],
    author_data: dict[str, dict[str, Any]],
    tags: list[dict[str, str]],
    repo: str,
    date_range: str,
    total_commits: int,
) -> str:
    """Render the dashboard HTML with the given payload baked in."""
    payload = {
        "all": all_data,
        "authors": author_data,
        "tags": tags,
        "repo": repo,
        "dateRange": date_range,
        "totalCommits": total_commits,
        "days": list(DAYS),
        "months": list(MONTHS),
        "cadence": release_cadence(tags),
    }
    data_json = json.dumps(payload, separators=(",", ":"))

    html, css, js = _load_template_parts()
    # Splice JSON in first; `replace` avoids any %/{ formatting issues.
    js_with_data = js.replace("{{DATA}}", data_json)
    return html.replace("{{STYLES}}", css).replace("{{SCRIPT}}", js_with_data)
