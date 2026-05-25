"""Unit tests for cadence helpers."""

from __future__ import annotations

from repostory.cadence import conv_type, release_cadence, rolling_avg


class TestConvType:
    def test_known_prefix(self) -> None:
        assert conv_type("feat: add login") == "feat"
        assert conv_type("fix(api): handle null") == "fix"

    def test_breaking_change_marker(self) -> None:
        assert conv_type("feat!: drop python 3.8") == "feat"

    def test_case_insensitive(self) -> None:
        assert conv_type("FIX: typo") == "fix"

    def test_unknown_prefix_is_other(self) -> None:
        assert conv_type("update: misc") == "other"

    def test_no_prefix_is_other(self) -> None:
        assert conv_type("just a sentence") == "other"
        assert conv_type("") == "other"


class TestRollingAvg:
    def test_window_smaller_than_data(self) -> None:
        weekly = [
            {"week": "2025-W01", "count": 4},
            {"week": "2025-W02", "count": 8},
            {"week": "2025-W03", "count": 12},
            {"week": "2025-W04", "count": 16},
            {"week": "2025-W05", "count": 20},
        ]
        result = rolling_avg(weekly, window=2)
        assert [r["avg"] for r in result] == [4.0, 6.0, 10.0, 14.0, 18.0]

    def test_empty_input(self) -> None:
        assert rolling_avg([]) == []

    def test_preserves_week_labels(self) -> None:
        weekly = [{"week": "2025-W01", "count": 1}]
        assert rolling_avg(weekly)[0]["week"] == "2025-W01"


class TestReleaseCadence:
    def test_too_few_tags(self) -> None:
        assert release_cadence([])["trend"] == "n/a"
        assert release_cadence([{"name": "v1", "date": "2025-01-01"}])["gaps"] == []

    def test_basic_stats(self, sample_tags: list[dict[str, str]]) -> None:
        rc = release_cadence(sample_tags)
        # 5 tags → 4 gaps in days: 10, 26, 14, 3 → sorted: 3, 10, 14, 26
        assert rc["gaps"] == [3, 10, 14, 26]
        assert rc["shortest"] == 3
        assert rc["longest"] == 26
        assert rc["median"] == 14  # gaps[len(gaps) // 2] == gaps[2]
        assert rc["trend"] in {"faster", "slower", "stable", "n/a"}
