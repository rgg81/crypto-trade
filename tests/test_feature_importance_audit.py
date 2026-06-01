"""Tests for analysis/feature_importance_audit.py — rank stability audit.

Covers:
1. test_compute_rank_stats_single_slice — one CSV, stats equal the CSV's ranks
2. test_compute_rank_stats_multi_slice — two CSVs, mean_rank = arithmetic average
3. test_build_drop_list_known — synthetic stats -> expected drop list
4. test_build_drop_list_nothing_to_drop — all features well-ranked -> empty list
5. test_find_feature_importance_csvs_single_seed — Layout B discovery
6. test_find_feature_importance_csvs_multi_seed — Layout A discovery
7. test_read_feature_importance_csv_importance_rank_column — direct importance_rank
8. test_read_feature_importance_csv_mean_gain_fallback — derives rank from mean_gain
9. test_format_audit_summary_contains_drop — markdown table contains DROP label
10. test_full_pipeline_cli_equivalent — end-to-end through public functions
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent.parent / "analysis"))

from feature_importance_audit import (  # noqa: E402
    build_drop_list,
    compute_rank_stats,
    find_feature_importance_csvs,
    format_audit_summary,
    read_feature_importance_csv,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_fi_csv(path: Path, features: list[str], ranks: list[int]) -> None:
    """Write a minimal feature_importance CSV with importance_rank column."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"feature_name": features, "importance_rank": ranks})
    df.to_csv(path, index=False)


def _write_fi_csv_gain(path: Path, features: list[str], gains: list[float]) -> None:
    """Write a feature_importance CSV with mean_gain column (no importance_rank)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"feature_name": features, "mean_gain": gains})
    df.to_csv(path, index=False)


# ---------------------------------------------------------------------------
# 1. compute_rank_stats — single slice
# ---------------------------------------------------------------------------


def test_compute_rank_stats_single_slice() -> None:
    """Single slice -> mean_rank == importance_rank, std_of_rank == 0."""
    features = ["feat_a", "feat_b", "feat_c"]
    ranks = [1, 2, 3]
    df = pd.DataFrame({"feature_name": features, "importance_rank": ranks})
    stats = compute_rank_stats([df])

    assert set(stats["feature_name"]) == set(features)
    # std_of_rank should be 0 (fillna after groupby std with single sample)
    for _, row in stats.iterrows():
        assert row["std_of_rank"] == 0.0, (
            f"{row['feature_name']}: expected std=0.0, got {row['std_of_rank']}"
        )
    # mean_rank should equal original rank
    row_a = stats[stats["feature_name"] == "feat_a"].iloc[0]
    assert row_a["mean_rank"] == 1.0


def test_compute_rank_stats_multi_slice() -> None:
    """Two slices with different ranks -> mean is arithmetic average."""
    # Slice 1: feat_a=1, feat_b=2, feat_c=3
    # Slice 2: feat_a=3, feat_b=1, feat_c=2
    # Expected means: feat_a=2.0, feat_b=1.5, feat_c=2.5
    slice1 = pd.DataFrame(
        {"feature_name": ["feat_a", "feat_b", "feat_c"], "importance_rank": [1, 2, 3]}
    )
    slice2 = pd.DataFrame(
        {"feature_name": ["feat_a", "feat_b", "feat_c"], "importance_rank": [3, 1, 2]}
    )
    stats = compute_rank_stats([slice1, slice2])

    means = dict(zip(stats["feature_name"], stats["mean_rank"]))
    assert abs(means["feat_a"] - 2.0) < 1e-9, f"feat_a mean expected 2.0, got {means['feat_a']}"
    assert abs(means["feat_b"] - 1.5) < 1e-9, f"feat_b mean expected 1.5, got {means['feat_b']}"
    assert abs(means["feat_c"] - 2.5) < 1e-9, f"feat_c mean expected 2.5, got {means['feat_c']}"


# ---------------------------------------------------------------------------
# 2. build_drop_list — synthetic stats
# ---------------------------------------------------------------------------


def test_build_drop_list_known() -> None:
    """Features with mean_rank >= 12 AND std_of_rank < 2.0 are dropped."""
    stats = pd.DataFrame(
        {
            "feature_name": ["good_feat", "borderline", "drop_me", "also_drop"],
            "mean_rank": [3.0, 12.0, 14.0, 13.5],
            "std_of_rank": [1.0, 3.0, 1.5, 0.5],  # borderline has std=3 > 2 -> kept
            "n_slices": [5, 5, 5, 5],
        }
    )
    drop_list = build_drop_list(stats, min_mean_rank=12.0, max_std_rank=2.0)
    # borderline: mean=12 BUT std=3.0 >= 2.0 -> NOT dropped
    # drop_me: mean=14 >= 12, std=1.5 < 2.0 -> dropped
    # also_drop: mean=13.5 >= 12, std=0.5 < 2.0 -> dropped
    assert "drop_me" in drop_list, f"Expected 'drop_me' in drop_list, got {drop_list}"
    assert "also_drop" in drop_list, f"Expected 'also_drop' in drop_list, got {drop_list}"
    assert "good_feat" not in drop_list, "'good_feat' should not be in drop_list"
    assert "borderline" not in drop_list, "'borderline' (high std) should not be in drop_list"
    assert len(drop_list) == 2


def test_build_drop_list_nothing_to_drop() -> None:
    """All features well-ranked -> drop list is empty."""
    stats = pd.DataFrame(
        {
            "feature_name": ["feat_a", "feat_b", "feat_c"],
            "mean_rank": [1.0, 5.0, 8.0],
            "std_of_rank": [0.5, 1.0, 1.5],
            "n_slices": [3, 3, 3],
        }
    )
    drop_list = build_drop_list(stats)
    assert drop_list == [], f"Expected empty drop list, got {drop_list}"


def test_build_drop_list_exact_boundary() -> None:
    """Boundary: mean_rank exactly == min_mean_rank is included."""
    stats = pd.DataFrame(
        {
            "feature_name": ["feat_boundary"],
            "mean_rank": [12.0],
            "std_of_rank": [1.0],
            "n_slices": [4],
        }
    )
    drop_list = build_drop_list(stats, min_mean_rank=12.0, max_std_rank=2.0)
    assert "feat_boundary" in drop_list, "mean_rank == threshold should be included (>=)"


# ---------------------------------------------------------------------------
# 3. find_feature_importance_csvs
# ---------------------------------------------------------------------------


def test_find_feature_importance_csvs_single_seed(tmp_path: Path) -> None:
    """Layout B: feature_importance CSV directly in in_sample/ -> discovered."""
    reports_dir = tmp_path / "iteration_v1-001"
    is_dir = reports_dir / "in_sample"
    is_dir.mkdir(parents=True)
    csv_path = is_dir / "feature_importance_portfolio.csv"
    _write_fi_csv(csv_path, ["feat_a"], [1])

    found = find_feature_importance_csvs(reports_dir)
    assert len(found) >= 1, f"Expected at least 1 CSV, got {len(found)}"
    assert any(p.name == "feature_importance_portfolio.csv" for p in found), (
        f"feature_importance_portfolio.csv not found in {found}"
    )


def test_find_feature_importance_csvs_multi_seed(tmp_path: Path) -> None:
    """Layout A: CSVs in seed_*/in_sample/ -> all discovered."""
    reports_dir = tmp_path / "iteration_v1-002"
    for seed_label in ["seed_42", "seed_offset3"]:
        csv_path = reports_dir / seed_label / "in_sample" / "feature_importance_portfolio.csv"
        _write_fi_csv(csv_path, ["feat_a", "feat_b"], [1, 2])

    found = find_feature_importance_csvs(reports_dir)
    assert len(found) == 2, f"Expected 2 CSVs (one per seed), got {len(found)}"


# ---------------------------------------------------------------------------
# 4. read_feature_importance_csv
# ---------------------------------------------------------------------------


def test_read_feature_importance_csv_importance_rank_column(tmp_path: Path) -> None:
    """CSV with importance_rank column is read directly."""
    csv_path = tmp_path / "feature_importance_portfolio.csv"
    _write_fi_csv(csv_path, ["feat_a", "feat_b", "feat_c"], [1, 2, 3])
    df = read_feature_importance_csv(csv_path)
    assert df is not None
    assert set(df.columns) == {"feature_name", "importance_rank"}
    assert len(df) == 3
    row_a = df[df["feature_name"] == "feat_a"].iloc[0]
    assert row_a["importance_rank"] == 1.0


def test_read_feature_importance_csv_mean_gain_fallback(tmp_path: Path) -> None:
    """CSV with mean_gain (no importance_rank) -> rank derived from gain descending."""
    csv_path = tmp_path / "feature_importance_portfolio.csv"
    # Higher gain -> lower rank (rank 1 = highest gain)
    _write_fi_csv_gain(csv_path, ["feat_low", "feat_mid", "feat_high"], [100.0, 500.0, 1000.0])
    df = read_feature_importance_csv(csv_path)
    assert df is not None
    row_high = df[df["feature_name"] == "feat_high"].iloc[0]
    row_low = df[df["feature_name"] == "feat_low"].iloc[0]
    assert row_high["importance_rank"] < row_low["importance_rank"], (
        "feat_high (1000 gain) should have lower importance_rank than feat_low (100 gain)"
    )


def test_read_feature_importance_csv_missing_file_returns_none(tmp_path: Path) -> None:
    """Non-existent file -> read function handles gracefully (returns None via exception)."""
    missing = tmp_path / "does_not_exist.csv"
    result = read_feature_importance_csv(missing)
    assert result is None


# ---------------------------------------------------------------------------
# 5. format_audit_summary
# ---------------------------------------------------------------------------


def test_format_audit_summary_contains_drop() -> None:
    """Markdown summary should contain DROP label for features in drop_list."""
    stats = pd.DataFrame(
        {
            "feature_name": ["keep_feat", "drop_feat"],
            "mean_rank": [2.0, 14.0],
            "std_of_rank": [1.0, 0.5],
            "n_slices": [3, 3],
        }
    )
    drop_list = ["drop_feat"]
    md = format_audit_summary(stats, drop_list, 12.0, 2.0, "042", 3)

    assert "DROP" in md, "Markdown should contain 'DROP' label for dropped features"
    assert "keep" in md, "Markdown should contain 'keep' label for retained features"
    assert "drop_feat" in md
    assert "keep_feat" in md
    assert "iter-v1/042" in md


# ---------------------------------------------------------------------------
# 6. Full pipeline test (end-to-end through public functions)
# ---------------------------------------------------------------------------


def test_full_pipeline_end_to_end(tmp_path: Path) -> None:
    """End-to-end: write synthetic CSVs, discover, read, compute stats, drop list.

    Scenario: 3 seeds, 5 features; feat_e is consistently ranked last (rank 5)
    with near-zero variance -> should appear in drop_list.
    """
    reports_dir = tmp_path / "iteration_v1-099"

    # Seed 1: feat_e rank 5
    s1_path = reports_dir / "seed_42" / "in_sample" / "feature_importance_portfolio.csv"
    _write_fi_csv(s1_path, ["feat_a", "feat_b", "feat_c", "feat_d", "feat_e"], [1, 2, 3, 4, 5])

    # Seed 2: feat_e rank 5
    s2_path = reports_dir / "seed_offset3" / "in_sample" / "feature_importance_portfolio.csv"
    _write_fi_csv(s2_path, ["feat_a", "feat_b", "feat_c", "feat_d", "feat_e"], [2, 1, 3, 4, 5])

    # Seed 3: feat_e rank 5
    s3_path = reports_dir / "seed_offset6" / "in_sample" / "feature_importance_portfolio.csv"
    _write_fi_csv(s3_path, ["feat_a", "feat_b", "feat_c", "feat_d", "feat_e"], [1, 3, 2, 4, 5])

    csvs = find_feature_importance_csvs(reports_dir)
    assert len(csvs) == 3, f"Expected 3 CSVs, got {len(csvs)}"

    slices = [read_feature_importance_csv(p) for p in csvs]
    slices = [s for s in slices if s is not None]
    assert len(slices) == 3

    stats = compute_rank_stats(slices)
    # feat_e should have mean_rank=5.0, std_of_rank=0.0 -> qualifies for drop
    row_e = stats[stats["feature_name"] == "feat_e"].iloc[0]
    assert abs(row_e["mean_rank"] - 5.0) < 1e-9, (
        f"feat_e mean_rank expected 5.0, got {row_e['mean_rank']}"
    )
    assert row_e["std_of_rank"] == 0.0, (
        f"feat_e std_of_rank expected 0.0, got {row_e['std_of_rank']}"
    )

    # With min_mean_rank=5.0 (exact boundary), feat_e should be dropped
    drop_list = build_drop_list(stats, min_mean_rank=5.0, max_std_rank=1.0)
    assert "feat_e" in drop_list, f"feat_e should be in drop_list, got {drop_list}"

    # feat_d has rank 4 in all slices -> mean=4, std=0 -> dropped at threshold 4.0
    drop_list_4 = build_drop_list(stats, min_mean_rank=4.0, max_std_rank=1.0)
    assert "feat_d" in drop_list_4, "feat_d should be in drop_list_4 at threshold 4.0"
    assert "feat_e" in drop_list_4
