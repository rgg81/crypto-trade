"""Tests for analysis/basin_diagnostics.py — automatic basin-lottery detection.

Covers:
1. test_per_seed_spread_correctness — synthetic 3-seed array -> known max-min
2. test_per_seed_spread_nan_handling — NaN values ignored, only 1 finite -> NaN
3. test_jaccard_median_known — synthetic trade sets -> known median pairwise overlap
4. test_jaccard_single_seed_returns_nan — fewer than 2 seeds -> NaN
5. test_lottery_verdict_thresholds_pass — all metrics in safe zone -> PASS
6. test_lottery_verdict_thresholds_weak — one metric in warn zone -> WEAK
7. test_lottery_verdict_thresholds_confirmed — one metric in fail zone -> CONFIRMED
8. test_cross_seed_param_spearman_perfect_agreement — identical dicts -> rho ~1.0
9. test_cross_seed_param_spearman_inverse — opposite ranks -> rho ~ -1.0
10. test_run_basin_diagnostics_single_seed_layout — CLI runner, Layout B
"""

from __future__ import annotations

import json
import math

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "analysis"))

from basin_diagnostics import (  # noqa: E402
    compute_basin_lottery_verdict,
    compute_cross_seed_param_spearman,
    compute_pairwise_jaccard,
    compute_per_seed_spread,
    run_basin_diagnostics,
)

# ---------------------------------------------------------------------------
# 1. test_per_seed_spread_correctness
# ---------------------------------------------------------------------------


def test_per_seed_spread_correctness() -> None:
    """Synthetic 3-seed array should yield exact max-min spread."""
    sharpes = [1.5, 0.2, -0.8]
    result = compute_per_seed_spread(sharpes)
    expected = 1.5 - (-0.8)  # 2.3
    assert math.isclose(result, expected, rel_tol=1e-9), f"Expected spread {expected}, got {result}"


def test_per_seed_spread_nan_handling() -> None:
    """NaN values in sharpe array should be ignored.

    If only 1 finite value remains, result must be NaN.
    If 2+ finite values remain, spread is computed correctly.
    """
    # Single finite value -> NaN
    result_nan = compute_per_seed_spread([float("nan"), 1.2, float("nan")])
    assert math.isnan(result_nan), f"Expected NaN for single finite value, got {result_nan}"

    # Two finite values -> correct spread
    result = compute_per_seed_spread([float("nan"), 1.5, -0.5])
    assert math.isclose(result, 2.0, rel_tol=1e-9), f"Expected 2.0, got {result}"


# ---------------------------------------------------------------------------
# 2. test_jaccard_median_known
# ---------------------------------------------------------------------------


def test_jaccard_median_known() -> None:
    """Synthetic trade sets with known pairwise Jaccard -> correct median.

    Seed A: {1, 2, 3, 4}
    Seed B: {3, 4, 5, 6}   J(A,B) = |{3,4}| / |{1,2,3,4,5,6}| = 2/6 = 0.333...
    Seed C: {1, 2, 3, 4}   J(A,C) = 4/4 = 1.0
                            J(B,C) = 2/6 = 0.333...
    Median of [0.333, 1.0, 0.333] = 0.333...
    """
    # Trade sets use (symbol, open_time) tuples; symbol is irrelevant for math
    a_set: set[tuple] = {("SYM", i) for i in [1, 2, 3, 4]}
    b_set: set[tuple] = {("SYM", i) for i in [3, 4, 5, 6]}
    c_set: set[tuple] = {("SYM", i) for i in [1, 2, 3, 4]}

    result = compute_pairwise_jaccard({"A": a_set, "B": b_set, "C": c_set})
    expected = 2.0 / 6.0  # median of [2/6, 1.0, 2/6]
    assert math.isclose(result, expected, rel_tol=1e-9), (
        f"Expected Jaccard median {expected:.4f}, got {result:.4f}"
    )


def test_jaccard_single_seed_returns_nan() -> None:
    """A dict with a single seed cannot produce pairwise statistics -> NaN."""
    result = compute_pairwise_jaccard({"seed_42": {("SYM", 1), ("SYM", 2)}})
    assert math.isnan(result), f"Expected NaN for single seed, got {result}"


def test_jaccard_empty_sets_produce_nan() -> None:
    """Both seeds with empty trade sets produce a union of 0 -> NaN Jaccard (not 0/0)."""
    result = compute_pairwise_jaccard({"A": set(), "B": set()})
    # union = 0 -> NaN, no valid pairwise values -> NaN
    assert math.isnan(result), f"Expected NaN for empty sets, got {result}"


# ---------------------------------------------------------------------------
# 3. test_lottery_verdict_thresholds
# ---------------------------------------------------------------------------


def test_lottery_verdict_pass() -> None:
    """All metrics in safe zone -> PASS."""
    verdict = compute_basin_lottery_verdict(
        spread=0.3,  # < 0.80 warn threshold
        jaccard_median=0.60,  # > 0.35 warn threshold
        spearman_rho=0.75,  # > 0.60 warn threshold
    )
    assert verdict == "PASS", f"Expected PASS, got {verdict}"


def test_lottery_verdict_weak_spread() -> None:
    """Spread in warn zone [0.80, 1.50) -> BASIN-LOTTERY-WEAK."""
    verdict = compute_basin_lottery_verdict(
        spread=1.0,  # >= 0.80, < 1.50
        jaccard_median=0.60,
        spearman_rho=0.75,
    )
    assert verdict == "BASIN-LOTTERY-WEAK", f"Expected BASIN-LOTTERY-WEAK, got {verdict}"


def test_lottery_verdict_confirmed_spread() -> None:
    """Spread in fail zone (>= 1.50) -> BASIN-LOTTERY-CONFIRMED."""
    verdict = compute_basin_lottery_verdict(
        spread=2.0,  # >= 1.50
        jaccard_median=0.60,
        spearman_rho=0.75,
    )
    assert verdict == "BASIN-LOTTERY-CONFIRMED", f"Expected BASIN-LOTTERY-CONFIRMED, got {verdict}"


def test_lottery_verdict_confirmed_jaccard() -> None:
    """Jaccard in fail zone (<= 0.15) -> BASIN-LOTTERY-CONFIRMED."""
    verdict = compute_basin_lottery_verdict(
        spread=0.3,
        jaccard_median=0.10,  # <= 0.15
        spearman_rho=0.75,
    )
    assert verdict == "BASIN-LOTTERY-CONFIRMED", f"Expected BASIN-LOTTERY-CONFIRMED, got {verdict}"


def test_lottery_verdict_nan_does_not_trigger() -> None:
    """NaN metrics should not trigger CONFIRMED or WEAK (conservative)."""
    # All NaN -> PASS (no evidence)
    verdict = compute_basin_lottery_verdict(
        spread=float("nan"),
        jaccard_median=float("nan"),
        spearman_rho=float("nan"),
    )
    assert verdict == "PASS", f"Expected PASS for all-NaN, got {verdict}"


# ---------------------------------------------------------------------------
# 4. test_cross_seed_param_spearman
# ---------------------------------------------------------------------------


def test_cross_seed_param_spearman_perfect_agreement() -> None:
    """Identical feature rank dicts across seeds -> Spearman rho = 1.0."""
    ranks = {"feat_a": 1.0, "feat_b": 2.0, "feat_c": 3.0, "feat_d": 4.0}
    result = compute_cross_seed_param_spearman({"seed_42": ranks, "seed_offset3": ranks})
    assert math.isclose(result, 1.0, rel_tol=1e-9), (
        f"Identical rank dicts should yield rho=1.0, got {result}"
    )


def test_cross_seed_param_spearman_inverse() -> None:
    """Reversed feature rank dicts -> Spearman rho = -1.0."""
    ranks_a = {"feat_a": 1.0, "feat_b": 2.0, "feat_c": 3.0, "feat_d": 4.0}
    ranks_b = {"feat_a": 4.0, "feat_b": 3.0, "feat_c": 2.0, "feat_d": 1.0}
    result = compute_cross_seed_param_spearman({"seed_42": ranks_a, "seed_offset3": ranks_b})
    assert math.isclose(result, -1.0, rel_tol=1e-9), (
        f"Reversed rank dicts should yield rho=-1.0, got {result}"
    )


def test_cross_seed_param_spearman_no_common_features() -> None:
    """No shared features across seeds -> NaN (no pairwise rho computable)."""
    result = compute_cross_seed_param_spearman(
        {
            "seed_42": {"feat_x": 1.0, "feat_y": 2.0},
            "seed_offset3": {"feat_a": 1.0, "feat_b": 2.0},
        }
    )
    # 0 common features -> no valid pairs with >= 3 shared keys -> NaN
    assert math.isnan(result), f"Expected NaN for no common features, got {result}"


# ---------------------------------------------------------------------------
# 5. test_run_basin_diagnostics_single_seed_layout
# ---------------------------------------------------------------------------


def _make_synthetic_reports_dir(tmp_path: Path) -> Path:
    """Create a minimal single-seed Layout B reports directory with synthetic data."""
    reports_dir = tmp_path / "iteration_v1-999"
    reports_dir.mkdir()

    # comparison.csv (Layout B: directly in reports_dir)
    comparison_csv = reports_dir / "comparison.csv"
    comparison_csv.write_text(
        "metric,in_sample,out_of_sample,ratio\nsharpe,1.2,0.85,0.708\nsortino,1.5,1.0,0.667\n"
    )

    # out_of_sample/trades.csv
    oos_dir = reports_dir / "out_of_sample"
    oos_dir.mkdir()
    trades_df = pd.DataFrame(
        {
            "symbol": ["BTCUSDT", "ETHUSDT", "BTCUSDT"],
            "open_time": [1_700_000_000_000, 1_700_200_000_000, 1_700_400_000_000],
            "close_time": [1_700_100_000_000, 1_700_300_000_000, 1_700_500_000_000],
            "pnl_pct": [0.5, -0.3, 0.8],
        }
    )
    trades_df.to_csv(oos_dir / "trades.csv", index=False)

    # in_sample/feature_importance_portfolio.csv
    is_dir = reports_dir / "in_sample"
    is_dir.mkdir()
    fi_df = pd.DataFrame(
        {
            "feature_name": [f"feat_{i}" for i in range(1, 6)],
            "mean_gain": [1000.0, 800.0, 600.0, 400.0, 200.0],
            "importance_rank": [1, 2, 3, 4, 5],
        }
    )
    fi_df.to_csv(is_dir / "feature_importance_portfolio.csv", index=False)

    return reports_dir


def test_run_basin_diagnostics_single_seed_layout(tmp_path: Path) -> None:
    """CLI runner with Layout B (single seed) writes extended basin_diagnostics.json."""
    reports_dir = _make_synthetic_reports_dir(tmp_path)
    output_dir = reports_dir / "basin_diagnostics"

    run_basin_diagnostics(reports_dir, output_dir=output_dir)

    # JSON must be written
    json_path = output_dir / "basin_diagnostics.json"
    assert json_path.exists(), f"basin_diagnostics.json not found at {json_path}"

    with open(json_path) as f:
        loaded = json.load(f)

    # All four new keys must be present
    for key in (
        "v1_per_seed_spread",
        "v1_jaccard_median",
        "v1_spearman_rho",
        "lottery_verdict",
        "lottery_action_taken",
    ):
        assert key in loaded, f"Expected key '{key}' in basin_diagnostics.json"

    # Single seed -> spread = NaN (stored as None in JSON)
    assert loaded["v1_per_seed_spread"] is None, (
        "Single seed: per_seed_spread must be None (NaN in JSON)"
    )

    # Verdict must be a valid string
    assert loaded["lottery_verdict"] in ("PASS", "BASIN-LOTTERY-WEAK", "BASIN-LOTTERY-CONFIRMED")

    # Action string must be non-empty
    assert isinstance(loaded["lottery_action_taken"], str)
    assert len(loaded["lottery_action_taken"]) > 0
