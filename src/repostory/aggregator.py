"""Aggregate raw commits into the structured payload consumed by the dashboard."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from typing import Any, Iterable

from .cadence import conv_type, rolling_avg
from .constants import (
    CONV_TYPES,
    DAYS,
    NIGHT_HOUR_END,
    NIGHT_HOUR_START,
    REWORK_RE,
    WEEKEND_START_DAY,
)
from .git_io import Commit

# Velocity classification thresholds (recent vs. previous 4-week window).
_VEL_UP = 1.10
_VEL_DOWN = 0.90

# Co-change coupling thresholds.
_COUPLING_MIN_COUNT = 3
_COUPLING_MIN_TOUCHES = 5
_COUPLING_MAX_FILES_PER_COMMIT = 10  # avoid n^2 blow-up on huge merges

_SIZE_BINS = (
    ("tiny", 10),
    ("small", 50),
    ("medium", 200),
    ("large", 500),
    ("massive", math.inf),
)


def _size_bin(commit: Commit) -> str:
    total = commit.added + commit.deleted
    for label, cap in _SIZE_BINS:
        if total < cap:
            return label
    return "massive"


def _is_night(hour: int) -> bool:
    return hour >= NIGHT_HOUR_START or hour <= NIGHT_HOUR_END


def _is_weekend(day: int) -> bool:
    return day >= WEEKEND_START_DAY


def _project_span(dates: list[str]) -> tuple[int, str]:
    if not dates:
        return 0, "—"
    fd = datetime.strptime(dates[0], "%Y-%m-%d")
    ld = datetime.strptime(dates[-1], "%Y-%m-%d")
    span_days = (ld - fd).days
    years, rem = divmod(span_days, 365)
    months = rem // 30
    if years and months:
        return span_days, f"{years}y {months}mo"
    if years:
        return span_days, f"{years}y"
    if months:
        return span_days, f"{months}mo"
    return span_days, f"{span_days}d"


def _best_streak(dates_sorted: list[str]) -> int:
    if not dates_sorted:
        return 0
    prev = datetime.strptime(dates_sorted[0], "%Y-%m-%d")
    cur = 1
    best = 1
    for ds in dates_sorted[1:]:
        dt = datetime.strptime(ds, "%Y-%m-%d")
        cur = cur + 1 if (dt - prev).days == 1 else 1
        best = max(best, cur)
        prev = dt
    return best


def _message_bins(lengths: list[int]) -> list[dict[str, Any]]:
    return [
        {"label": "lazy (<15)", "count": sum(1 for l in lengths if l < 15)},
        {"label": "short", "count": sum(1 for l in lengths if 15 <= l < 40)},
        {"label": "good", "count": sum(1 for l in lengths if 40 <= l < 72)},
        {"label": "long (72+)", "count": sum(1 for l in lengths if l >= 72)},
    ]


def _conv_type_counts(commits: Iterable[Commit]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for c in commits:
        counts[conv_type(c.subject)] += 1
    result = {t: counts[t] for t in CONV_TYPES if counts[t]}
    if counts.get("other"):
        result["other"] = counts["other"]
    return result


def _velocity_trend(weekly_counts: list[int]) -> str:
    if len(weekly_counts) < 8:
        return "stable"
    recent = sum(weekly_counts[-4:]) / 4
    prev = sum(weekly_counts[-8:-4]) / 4
    if recent > prev * _VEL_UP:
        return "up"
    if recent < prev * _VEL_DOWN:
        return "down"
    return "stable"


def _consistency(weekly_counts: list[int]) -> int:
    if len(weekly_counts) <= 1:
        return 100
    mean = sum(weekly_counts) / len(weekly_counts)
    if not mean:
        return 100
    variance = sum((c - mean) ** 2 for c in weekly_counts) / len(weekly_counts)
    sd = math.sqrt(variance)
    return round(max(0, 1 - min(sd / mean, 1)) * 100)


def _gini(sorted_counts: list[int]) -> float:
    n = len(sorted_counts)
    total = sum(sorted_counts)
    if n <= 1 or total <= 0:
        return 0.0
    g = 1 - 2 * sum((n - i) * v for i, v in enumerate(sorted_counts)) / (n * total)
    return round(max(0.0, min(1.0, g)), 3)


def _lorenz(sorted_counts: list[int]) -> list[dict[str, float]]:
    total = sum(sorted_counts)
    if not sorted_counts or not total:
        return []
    n = len(sorted_counts)
    pts: list[dict[str, float]] = []
    cum = 0
    for i, v in enumerate(sorted_counts):
        cum += v
        pts.append({
            "x": round((i + 1) / n * 100, 1),
            "y": round(cum / total * 100, 1),
        })
    return pts


def _file_level_analysis(commits: list[Commit]) -> dict[str, Any]:
    """Compute size distribution, hotspots, coupling, and directory freshness."""
    size_dist: dict[str, int] = defaultdict(int)
    file_commit_count: dict[str, int] = defaultdict(int)
    file_author_set: dict[str, set[str]] = defaultdict(set)
    dir_last_touch: dict[str, str] = {}

    for c in commits:
        size_dist[_size_bin(c)] += 1
        for f in c.files:
            top = f.path.split("/")[0] if "/" in f.path else "(root)"
            file_commit_count[f.path] += 1
            file_author_set[f.path].add(c.author)
            if top not in dir_last_touch or c.date > dir_last_touch[top]:
                dir_last_touch[top] = c.date

    size_dist_list = [
        {"label": "tiny", "range": "<10 lines", "count": size_dist["tiny"]},
        {"label": "small", "range": "10-50", "count": size_dist["small"]},
        {"label": "medium", "range": "50-200", "count": size_dist["medium"]},
        {"label": "large", "range": "200-500", "count": size_dist["large"]},
        {"label": "massive", "range": "500+", "count": size_dist["massive"]},
    ]
    avg_size = (
        sum(c.added + c.deleted for c in commits) // len(commits) if commits else 0
    )
    total_added = sum(c.added for c in commits)
    total_deleted = sum(c.deleted for c in commits)

    hotspot_files = [
        {"path": p, "commits": n, "authors": len(file_author_set[p])}
        for p, n in sorted(file_commit_count.items(), key=lambda x: -x[1])[:20]
    ]

    cochange_count: dict[tuple[str, str], int] = defaultdict(int)
    for c in commits:
        paths = sorted({f.path for f in c.files})[:_COUPLING_MAX_FILES_PER_COMMIT]
        for pair in combinations(paths, 2):
            cochange_count[pair] += 1

    coupling: list[dict[str, Any]] = []
    for (fa, fb), count in cochange_count.items():
        total_touches = max(file_commit_count.get(fa, 1), file_commit_count.get(fb, 1))
        if count >= _COUPLING_MIN_COUNT and total_touches >= _COUPLING_MIN_TOUCHES:
            coupling.append(
                {
                    "a": fa,
                    "b": fb,
                    "count": count,
                    "pct": round(count / total_touches * 100),
                }
            )
    coupling = sorted(coupling, key=lambda x: -x["pct"])[:15]

    today = datetime.now()
    file_age = sorted(
        [
            {
                "dir": d,
                "lastTouch": dt,
                "daysSince": (today - datetime.strptime(dt, "%Y-%m-%d")).days,
            }
            for d, dt in dir_last_touch.items()
        ],
        key=lambda x: -x["daysSince"],
    )[:20]

    return {
        "sizeDist": size_dist_list,
        "avgSize": avg_size,
        "totalAdded": total_added,
        "totalDeleted": total_deleted,
        "hotspotFiles": hotspot_files,
        "coupledFiles": coupling,
        "fileAge": file_age,
    }


def _directory_attribution(commits: list[Commit]) -> tuple[
    dict[str, set[str]],
    dict[str, int],
    dict[str, dict[str, int]],
]:
    dir_authors: dict[str, set[str]] = defaultdict(set)
    dir_commits: dict[str, int] = defaultdict(int)
    author_dir: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in commits:
        dirs_seen: set[str] = set()
        for f in c.files:
            top = f.path.split("/")[0] if "/" in f.path else "(root)"
            dir_authors[top].add(c.author)
            dirs_seen.add(top)
            dir_commits[top] += 1
        for d in dirs_seen:
            author_dir[c.author][d] += 1
    return dir_authors, dir_commits, author_dir


def agg(commits: list[Commit]) -> dict[str, Any]:
    """Convert a list of commits into the dashboard payload."""
    heatmap: dict[tuple[int, int], int] = defaultdict(int)
    hourly: dict[int, int] = defaultdict(int)
    daily: dict[int, int] = defaultdict(int)
    weekly: dict[str, int] = defaultdict(int)
    monthly: dict[str, int] = defaultdict(int)
    by_date: dict[str, int] = defaultdict(int)
    author_first: dict[str, str] = {}
    author_last: dict[str, str] = {}
    wlb_by_month: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "night": 0, "weekend": 0}
    )
    msg_by_month: dict[str, list[int]] = defaultdict(list)
    hour_lines: dict[int, list[int]] = defaultdict(list)

    for c in commits:
        heatmap[(c.day, c.hour)] += 1
        hourly[c.hour] += 1
        daily[c.day] += 1
        weekly[c.week] += 1
        monthly[c.month] += 1
        by_date[c.date] += 1
        if c.author not in author_first or c.date < author_first[c.author]:
            author_first[c.author] = c.date
        if c.author not in author_last or c.date > author_last[c.author]:
            author_last[c.author] = c.date
        m = c.month
        wlb_by_month[m]["total"] += 1
        if _is_night(c.hour):
            wlb_by_month[m]["night"] += 1
        if _is_weekend(c.day):
            wlb_by_month[m]["weekend"] += 1
        msg_by_month[m].append(len(c.subject))
        if c.added or c.deleted:
            hour_lines[c.hour].append(c.added + c.deleted)

    hm = [
        {"day": d, "hour": h, "count": heatmap[(d, h)]}
        for d in range(7)
        for h in range(24)
    ]
    hl = [{"hour": h, "count": hourly[h]} for h in range(24)]
    dl = [{"day": d, "name": DAYS[d], "count": daily[d]} for d in range(7)]

    all_weeks = sorted(weekly.keys())
    wl = [{"week": w, "count": weekly[w]} for w in all_weeks]
    rolling = rolling_avg(wl)

    all_months = sorted(monthly.keys())
    ml = [
        {"month": m, "label": m[5:] + "/" + m[2:4], "count": monthly[m]}
        for m in all_months
    ]

    top_dates_raw = sorted(by_date.items(), key=lambda x: -x[1])[:10]
    td = [
        {
            "date": d,
            "count": n,
            "dayName": DAYS[datetime.strptime(d, "%Y-%m-%d").weekday()],
        }
        for d, n in top_dates_raw
    ]
    cal = [{"date": d, "count": n} for d, n in sorted(by_date.items())]

    all_dates = sorted(by_date.keys())
    best_streak = _best_streak(all_dates)
    active_days = len(by_date)
    total = sum(hourly.values())
    night = sum(n for h, n in hourly.items() if _is_night(h))
    weekend = sum(n for d, n in daily.items() if _is_weekend(d))
    span_days, span_label = _project_span(all_dates)

    conv_types = _conv_type_counts(commits)

    rework_count = sum(1 for c in commits if REWORK_RE.search(c.subject))
    revert_count = sum(1 for c in commits if c.subject.lower().startswith("revert"))
    rework_rate = round(rework_count / total * 100) if total else 0

    lengths = [len(c.subject) for c in commits]
    avg_len = round(sum(lengths) / len(lengths)) if lengths else 0
    lazy_pct = (
        round(sum(1 for l in lengths if l < 15) / len(lengths) * 100) if lengths else 0
    )
    msg_bins = _message_bins(lengths)

    has_stat = any(c.files for c in commits)
    file_stats = (
        _file_level_analysis(commits)
        if has_stat
        else {
            "sizeDist": [],
            "avgSize": 0,
            "totalAdded": 0,
            "totalDeleted": 0,
            "hotspotFiles": [],
            "coupledFiles": [],
            "fileAge": [],
        }
    )

    dir_authors, dir_commits, author_dir = _directory_attribution(commits)
    bus_factor = sorted(
        [
            {
                "dir": d,
                "authors": len(a),
                "commits": dir_commits[d],
                "authorList": sorted(a)[:3],
            }
            for d, a in dir_authors.items()
        ],
        key=lambda x: -x["commits"],
    )[:20]

    author_totals: dict[str, int] = defaultdict(int)
    for c in commits:
        author_totals[c.author] += 1
    top_authors = [a for a, _ in sorted(author_totals.items(), key=lambda x: -x[1])[:8]]
    top_dirs = [d for d, _ in sorted(dir_commits.items(), key=lambda x: -x[1])[:12]]
    adm = [
        {"author": a, "dirs": {d: author_dir[a][d] for d in top_dirs}}
        for a in top_authors
    ]

    sorted_counts = sorted(author_totals.values())
    gini_val = _gini(sorted_counts)
    lorenz_pts = _lorenz(sorted_counts)

    tenure_list = sorted(
        [
            {
                "author": a,
                "first": author_first[a],
                "last": author_last[a],
                "commits": author_totals[a],
            }
            for a in author_totals
            if a in author_first
        ],
        key=lambda x: x["first"],
    )

    cohort_dict: dict[str, int] = defaultdict(int)
    for a in author_first:
        cohort_dict[author_first[a][:7]] += 1
    cohorts = [{"month": m, "count": cohort_dict[m]} for m in sorted(cohort_dict)]

    wlb_trend = [
        {
            "month": m,
            "nightPct": round(v["night"] / v["total"] * 100) if v["total"] else 0,
            "weekendPct": round(v["weekend"] / v["total"] * 100) if v["total"] else 0,
        }
        for m, v in sorted(wlb_by_month.items())
    ]

    msg_trend = [
        {"month": m, "avgLen": round(sum(ls) / len(ls)) if ls else 0}
        for m, ls in sorted(msg_by_month.items())
    ]

    hour_size = [
        {
            "hour": h,
            "avgLines": (
                round(sum(hour_lines[h]) / len(hour_lines[h])) if hour_lines[h] else 0
            ),
        }
        for h in range(24)
    ]

    weekly_counts = [w["count"] for w in wl]
    vel_trend = _velocity_trend(weekly_counts)
    consistency = _consistency(weekly_counts)

    peak_hour = max(hourly, key=hourly.get) if hourly else 0
    peak_day = max(daily, key=daily.get) if daily else 0
    peak_date = max(by_date, key=by_date.get) if by_date else ""
    peak_date_count = by_date.get(peak_date, 0)
    conv_peak = max(conv_types, key=conv_types.get) if conv_types else "—"

    stats = {
        "total": total,
        "peakHour": peak_hour,
        "peakDay": peak_day,
        "peakDate": peak_date,
        "peakDateCount": peak_date_count,
        "streak": best_streak,
        "activeDays": active_days,
        "nightPct": round(night / total * 100) if total else 0,
        "weekendPct": round(weekend / total * 100) if total else 0,
        "avgPerDay": round(total / active_days, 1) if active_days else 0,
        "spanDays": span_days,
        "spanLabel": span_label,
        "reworkRate": rework_rate,
        "revertCount": revert_count,
        "avgSize": file_stats["avgSize"],
        "totalAdded": file_stats["totalAdded"],
        "totalDeleted": file_stats["totalDeleted"],
        "convPeak": conv_peak,
        "msgAvgLen": avg_len,
        "msgLazyPct": lazy_pct,
        "velTrend": vel_trend,
        "consistency": consistency,
        "hasStat": has_stat,
    }

    return {
        "heatmap": hm,
        "hourly": hl,
        "daily": dl,
        "weekly": wl,
        "rolling": rolling,
        "monthly": ml,
        "topDates": td,
        "calendar": cal,
        "stats": stats,
        "convTypes": conv_types,
        "sizeDist": file_stats["sizeDist"],
        "busFactor": bus_factor,
        "authorDirMatrix": adm,
        "dirList": top_dirs,
        "msgBins": msg_bins,
        "gini": gini_val,
        "lorenz": lorenz_pts,
        "authorTenure": tenure_list,
        "contributorCohorts": cohorts,
        "wlbTrend": wlb_trend,
        "msgTrend": msg_trend,
        "hourlySize": hour_size,
        "hotspotFiles": file_stats["hotspotFiles"],
        "coupledFiles": file_stats["coupledFiles"],
        "fileAge": file_stats["fileAge"],
    }


def per_author(commits: list[Commit]) -> dict[str, dict[str, Any]]:
    """Run agg() for each individual author."""
    by_author: dict[str, list[Commit]] = defaultdict(list)
    for c in commits:
        by_author[c.author].append(c)
    return {a: agg(cs) for a, cs in by_author.items()}
