"""Tests for H8/H9 fix: IS/OOS dispersion split + post-veto append.

Verifies that:
  1. _specialist_dispersion_stats entries are dicts with open_time_ms,
     signed_weight_std, and period keys.
  2. set_period() controls the period tag on subsequent appends.
  3. persist_specialist_dispersion_csv(path, period="IS") writes only IS rows.
  4. persist_specialist_dispersion_csv(path, period="OOS") writes only OOS rows.
  5. IS and OOS output files are byte-distinct when both periods have signals.
  6. get_specialist_dispersion_mean(period=...) filters correctly.
  7. write_specialist_dispersion_csvs() helper produces the correct split.
"""

from __future__ import annotations

import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_strategy():
    """Return a LightGbmStrategy with specialist_mode=True, minimal config."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    return LightGbmStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=["f0", "f1", "f2"],
        specialist_mode=True,
    )


def _inject_is_oos_samples(strat, n_is: int = 3, n_oos: int = 2) -> None:
    """Populate _specialist_dispersion_stats with n_is IS + n_oos OOS dicts."""
    base_ts = 1_700_000_000_000  # arbitrary epoch ms
    for i in range(n_is):
        strat._specialist_dispersion_stats.append(
            {
                "open_time_ms": base_ts + i * 28_800_000,
                "signed_weight_std": float(10 + i),
                "period": "IS",
            }
        )
    for i in range(n_oos):
        strat._specialist_dispersion_stats.append(
            {
                "open_time_ms": base_ts + (n_is + i) * 28_800_000,
                "signed_weight_std": float(50 + i),
                "period": "OOS",
            }
        )


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


def test_dispersion_entries_are_dicts() -> None:
    """_specialist_dispersion_stats entries must be dicts with required keys."""
    strat = _make_strategy()
    strat._specialist_dispersion_stats.append(
        {"open_time_ms": 1_700_000_000_000, "signed_weight_std": 42.0, "period": "IS"}
    )
    entry = strat._specialist_dispersion_stats[0]
    assert isinstance(entry, dict), "Entry must be a dict"
    assert "open_time_ms" in entry
    assert "signed_weight_std" in entry
    assert "period" in entry


def test_set_period_changes_current_period() -> None:
    """set_period() must update _current_period to the given value."""
    strat = _make_strategy()
    assert strat._current_period == "IS", "Default period must be 'IS'"
    strat.set_period("OOS")
    assert strat._current_period == "OOS"
    strat.set_period("IS")
    assert strat._current_period == "IS"


def test_set_period_rejects_invalid_value() -> None:
    """set_period() raises ValueError for unrecognised values."""
    import pytest

    strat = _make_strategy()
    with pytest.raises(ValueError, match="period must be 'IS' or 'OOS'"):
        strat.set_period("UNKNOWN")


def test_get_specialist_dispersion_mean_filters_by_period() -> None:
    """get_specialist_dispersion_mean(period=...) filters to the named period."""
    import numpy as np

    strat = _make_strategy()
    _inject_is_oos_samples(strat, n_is=3, n_oos=2)

    is_vals = [10.0, 11.0, 12.0]
    oos_vals = [50.0, 51.0]

    mean_is = strat.get_specialist_dispersion_mean(period="IS")
    mean_oos = strat.get_specialist_dispersion_mean(period="OOS")
    mean_all = strat.get_specialist_dispersion_mean()

    assert mean_is is not None
    assert abs(mean_is - float(np.mean(is_vals))) < 1e-9, f"IS mean {mean_is}"

    assert mean_oos is not None
    assert abs(mean_oos - float(np.mean(oos_vals))) < 1e-9, f"OOS mean {mean_oos}"

    assert mean_all is not None
    assert abs(mean_all - float(np.mean(is_vals + oos_vals))) < 1e-9, f"all mean {mean_all}"


def test_get_specialist_dispersion_mean_period_with_no_entries_returns_none() -> None:
    """get_specialist_dispersion_mean(period='OOS') returns None if no OOS rows exist."""
    strat = _make_strategy()
    # Only IS entries
    _inject_is_oos_samples(strat, n_is=2, n_oos=0)

    assert strat.get_specialist_dispersion_mean(period="IS") is not None
    assert strat.get_specialist_dispersion_mean(period="OOS") is None


def test_dispersion_split_by_period(tmp_path: Path) -> None:
    """IS and OOS dispersion files contain distinct rows (H8/H9 core check).

    Mocks IS + OOS sample entries in _specialist_dispersion_stats, then
    calls persist_specialist_dispersion_csv with period='IS' and period='OOS'.
    Verifies:
      - IS file has exactly n_is data rows (excluding header).
      - OOS file has exactly n_oos data rows.
      - IS and OOS files are byte-distinct.
      - IS file does not contain any OOS open_time_ms values.
      - OOS file does not contain any IS open_time_ms values.
    """
    strat = _make_strategy()
    n_is, n_oos = 3, 2
    _inject_is_oos_samples(strat, n_is=n_is, n_oos=n_oos)

    is_path = tmp_path / "in_sample" / "specialist_dispersion.csv"
    oos_path = tmp_path / "out_of_sample" / "specialist_dispersion.csv"

    strat.persist_specialist_dispersion_csv(str(is_path), period="IS")
    strat.persist_specialist_dispersion_csv(str(oos_path), period="OOS")

    assert is_path.exists(), "IS dispersion CSV must exist"
    assert oos_path.exists(), "OOS dispersion CSV must exist"

    # Row count check.
    is_rows = list(csv.DictReader(is_path.read_text().splitlines()))
    oos_rows = list(csv.DictReader(oos_path.read_text().splitlines()))
    assert len(is_rows) == n_is, f"IS CSV must have {n_is} data rows; got {len(is_rows)}"
    assert len(oos_rows) == n_oos, f"OOS CSV must have {n_oos} data rows; got {len(oos_rows)}"

    # Byte-distinctness.
    assert is_path.read_bytes() != oos_path.read_bytes(), "IS and OOS files must be byte-distinct"

    # Cross-contamination check: IS timestamps must not appear in OOS file.
    is_timestamps = {r["open_time_ms"] for r in is_rows}
    oos_timestamps = {r["open_time_ms"] for r in oos_rows}
    assert is_timestamps.isdisjoint(oos_timestamps), (
        f"IS and OOS timestamp sets must be disjoint; overlap: {is_timestamps & oos_timestamps}"
    )

    # Column schema check.
    expected_cols = {"observation_idx", "open_time_ms", "signed_weight_std"}
    assert set(is_rows[0].keys()) == expected_cols, f"IS CSV columns: {set(is_rows[0].keys())}"
    assert set(oos_rows[0].keys()) == expected_cols, f"OOS CSV columns: {set(oos_rows[0].keys())}"


def test_dispersion_empty_period_writes_header_only(tmp_path: Path) -> None:
    """When a period has no entries, the CSV is written with header only (no crash)."""
    strat = _make_strategy()
    # Only IS entries — OOS will be empty.
    _inject_is_oos_samples(strat, n_is=2, n_oos=0)

    oos_path = tmp_path / "out_of_sample" / "specialist_dispersion.csv"
    strat.persist_specialist_dispersion_csv(str(oos_path), period="OOS")

    assert oos_path.exists()
    rows = list(csv.DictReader(oos_path.read_text().splitlines()))
    assert rows == [], "Empty-period CSV must have zero data rows"


def test_write_specialist_dispersion_csvs_helper(tmp_path: Path) -> None:
    """write_specialist_dispersion_csvs() produces correct IS + OOS split."""
    from crypto_trade.strategies.ml.reporting_v1 import write_specialist_dispersion_csvs

    strat = _make_strategy()
    n_is, n_oos = 4, 3
    _inject_is_oos_samples(strat, n_is=n_is, n_oos=n_oos)

    is_path = tmp_path / "in_sample" / "specialist_dispersion.csv"
    oos_path = tmp_path / "out_of_sample" / "specialist_dispersion.csv"

    write_specialist_dispersion_csvs(strat, is_path, oos_path)

    is_rows = list(csv.DictReader(is_path.read_text().splitlines()))
    oos_rows = list(csv.DictReader(oos_path.read_text().splitlines()))

    assert len(is_rows) == n_is
    assert len(oos_rows) == n_oos
    assert is_path.read_bytes() != oos_path.read_bytes()
