"""Smoke tests for the aggregation pipeline."""

from __future__ import annotations

from repostory.aggregator import agg, per_author
from repostory.git_io import Commit


class TestAgg:
    def test_total_commit_count(self, sample_commits: list[Commit]) -> None:
        result = agg(sample_commits)
        assert result["stats"]["total"] == len(sample_commits)

    def test_hourly_buckets_cover_24h(self, sample_commits: list[Commit]) -> None:
        hl = agg(sample_commits)["hourly"]
        assert len(hl) == 24
        assert [r["hour"] for r in hl] == list(range(24))

    def test_daily_buckets_cover_week(self, sample_commits: list[Commit]) -> None:
        dl = agg(sample_commits)["daily"]
        assert len(dl) == 7
        assert {r["name"] for r in dl} == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

    def test_heatmap_has_168_cells(self, sample_commits: list[Commit]) -> None:
        assert len(agg(sample_commits)["heatmap"]) == 7 * 24

    def test_file_stats_present(self, sample_commits: list[Commit]) -> None:
        stats = agg(sample_commits)["stats"]
        assert stats["hasStat"] is True
        assert stats["totalAdded"] > 0
        assert stats["avgSize"] > 0

    def test_conventional_commit_classification(self, sample_commits: list[Commit]) -> None:
        ct = agg(sample_commits)["convTypes"]
        # Fixture: 2 feat, 1 fix (one is "fix typo" without colon → "other"), 1 refactor, 1 docs
        assert ct.get("feat", 0) == 2
        assert ct.get("docs", 0) == 1
        assert ct.get("refactor", 0) == 1

    def test_rework_rate_nonzero(self, sample_commits: list[Commit]) -> None:
        # "fix:" and "fix typo" both match REWORK_RE
        assert agg(sample_commits)["stats"]["reworkRate"] > 0

    def test_bus_factor_buckets_by_top_level_dir(
        self, sample_commits: list[Commit]
    ) -> None:
        bf = agg(sample_commits)["busFactor"]
        by_dir = {row["dir"]: row for row in bf}
        # README.md has no "/" → falls into the "(root)" bucket, owned only by bob
        assert by_dir["(root)"]["authors"] == 1
        # All src/* files in the fixture are touched only by alice
        assert by_dir["src"]["authors"] == 1

    def test_gini_in_unit_interval(self, sample_commits: list[Commit]) -> None:
        gini = agg(sample_commits)["gini"]
        assert 0.0 <= gini <= 1.0

    def test_empty_commits(self) -> None:
        result = agg([])
        assert result["stats"]["total"] == 0
        assert result["stats"]["hasStat"] is False
        assert result["calendar"] == []
        assert result["weekly"] == []


class TestPerAuthor:
    def test_one_entry_per_author(self, sample_commits: list[Commit]) -> None:
        result = per_author(sample_commits)
        assert set(result) == {"alice@x.com", "bob@x.com"}

    def test_per_author_totals_sum_to_global(
        self, sample_commits: list[Commit]
    ) -> None:
        per = per_author(sample_commits)
        global_total = agg(sample_commits)["stats"]["total"]
        assert sum(d["stats"]["total"] for d in per.values()) == global_total
