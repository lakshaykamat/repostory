"""Pure helpers: release cadence, rolling averages, conventional-commit parsing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .constants import CONV_RE, CONV_TYPES

_FASTER_THRESHOLD = 0.85
_SLOWER_THRESHOLD = 1.15


def rolling_avg(weekly: list[dict[str, Any]], window: int = 4) -> list[dict[str, Any]]:
    """Trailing-window mean of weekly commit counts."""
    counts = [w["count"] for w in weekly]
    out: list[dict[str, Any]] = []
    for i, w in enumerate(weekly):
        lo = max(0, i - window + 1)
        chunk = counts[lo : i + 1]
        out.append({"week": w["week"], "avg": round(sum(chunk) / len(chunk), 1)})
    return out


def conv_type(subject: str) -> str:
    """Classify a commit subject by its conventional-commit prefix."""
    m = CONV_RE.match(subject)
    if not m:
        return "other"
    t = m.group(1).lower()
    return t if t in CONV_TYPES else "other"


def release_cadence(tags: list[dict[str, str]]) -> dict[str, Any]:
    """Summarize gaps between dated release tags."""
    if len(tags) < 2:
        return {"median": 0, "longest": 0, "shortest": 0, "trend": "n/a", "gaps": []}

    dates = [datetime.strptime(t["date"], "%Y-%m-%d") for t in tags]
    gaps = sorted((dates[i + 1] - dates[i]).days for i in range(len(dates) - 1))
    median = gaps[len(gaps) // 2]
    half = len(gaps) // 2

    if half >= 2:
        first_avg = sum(gaps[:half]) / half
        second_avg = sum(gaps[half:]) / half
        if second_avg < first_avg * _FASTER_THRESHOLD:
            trend = "faster"
        elif second_avg > first_avg * _SLOWER_THRESHOLD:
            trend = "slower"
        else:
            trend = "stable"
    else:
        trend = "n/a"

    return {
        "median": median,
        "longest": max(gaps),
        "shortest": min(gaps),
        "trend": trend,
        "gaps": gaps,
    }
