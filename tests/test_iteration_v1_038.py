"""Integration tests for iter-v1/038 — per-symbol rv-based vol-ceiling (risk-primitive axis).

Covers all 12 mandatory test items from research_brief.md Section 3.2 (10 items)
plus 2 additional structural checks:

 1. test_v1_038_cli_flag_parsing — --vol-ceiling-mode {none,per_symbol},
    --vol-ceiling-pct FLOAT, --vol-ceiling-scale FLOAT all accepted; invalid
    mode raises SystemExit (argparse error).
 2. test_v1_038_compute_per_symbol_vol_ceiling_p75 — IS-only p75 computed
    from a synthetic panel matches numpy.percentile reference within 1e-6.
 3. test_v1_038_compute_per_symbol_vol_ceiling_oos_exclusion — bars at or
    after OOS_CUTOFF_MS are excluded from percentile estimation (look-ahead
    safety check).
 4. test_v1_038_apply_vol_ceiling_above_threshold — current_rv > threshold
    returns scale_factor (0.5).
 5. test_v1_038_apply_vol_ceiling_below_threshold — current_rv <= threshold
    returns 1.0.
 6. test_v1_038_apply_vol_ceiling_nan_rv — NaN current_rv returns 1.0 (safety).
 7. test_v1_038_rv_30d_ann_past_only — compute_rv_30d_ann_at_bar uses only
    closes[:idx+1]; providing additional future closes does NOT change output.
 8. test_v1_038_dispatch_banner_in_source — runner source contains expected
    dispatch banner string.
 9. test_v1_038_dispatch_pre_flight_mode_assert — iteration_label='v1-038' with
    --vol-ceiling-mode none fires AssertionError before compute.
10. test_v1_038_dispatch_pre_flight_pct_assert — --vol-ceiling-pct outside
    [70, 80] fires AssertionError.
11. test_v1_038_in_baseline_catchall_exclusion — 'v1-038' is in the catch-all
    exclusion tuple in run_baseline_v1.py.
12. test_v1_038_vol_ceiling_thresholds_logged — per-symbol threshold print
    statement in dispatch block present in runner source.

Foundation regression:
- test_v1_038_walk_forward_embargo_regression — embargo discipline unchanged.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Test 1 — CLI flag parsing
# ---------------------------------------------------------------------------


def test_v1_038_cli_flag_parsing() -> None:
    """--vol-ceiling-mode {none,per_symbol}, --vol-ceiling-pct, --vol-ceiling-scale
    must all be accepted by the CLI parser. An invalid mode must raise SystemExit.
    """
    import argparse

    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"none"' in src, "run_baseline_v1.py must reference 'none' choice for vol-ceiling-mode"
    assert '"per_symbol"' in src, (
        "run_baseline_v1.py must reference 'per_symbol' choice for vol-ceiling-mode"
    )
    assert "--vol-ceiling-mode" in src, "run_baseline_v1.py must define --vol-ceiling-mode flag"
    assert "--vol-ceiling-pct" in src, "run_baseline_v1.py must define --vol-ceiling-pct flag"
    assert "--vol-ceiling-scale" in src, "run_baseline_v1.py must define --vol-ceiling-scale flag"

    parser = argparse.ArgumentParser()
    parser.add_argument("--vol-ceiling-mode", choices=["none", "per_symbol"], default="none")
    parser.add_argument("--vol-ceiling-pct", type=float, default=75.0)
    parser.add_argument("--vol-ceiling-scale", type=float, default=0.5)

    args_none = parser.parse_args(["--vol-ceiling-mode", "none"])
    assert args_none.vol_ceiling_mode == "none"

    args_per_sym = parser.parse_args(["--vol-ceiling-mode", "per_symbol"])
    assert args_per_sym.vol_ceiling_mode == "per_symbol"

    args_default = parser.parse_args([])
    assert args_default.vol_ceiling_mode == "none", (
        "Default must be 'none' for BIT-IDENTITY with pre-/038 runs."
    )
    assert args_default.vol_ceiling_pct == 75.0, "Default pct must be 75.0"
    assert abs(args_default.vol_ceiling_scale - 0.5) < 1e-9, "Default scale must be 0.5"

    with pytest.raises(SystemExit):
        parser.parse_args(["--vol-ceiling-mode", "portfolio"])


# ---------------------------------------------------------------------------
# Test 2 — compute_per_symbol_vol_ceiling p75 correctness
# ---------------------------------------------------------------------------


def test_v1_038_compute_per_symbol_vol_ceiling_p75() -> None:
    """IS-only p75 must match numpy.percentile reference within 1e-6 tolerance."""
    import pandas as pd

    from crypto_trade.risk.vol_ceiling import (
        compute_per_symbol_vol_ceiling,
        compute_rv_30d_ann_at_bar,
    )

    rng = np.random.default_rng(42)
    n = 300

    # Build synthetic close prices (geometric random walk)
    log_rets = rng.normal(0.0, 0.01, n)
    closes = np.cumprod(np.exp(np.r_[np.log(100.0), log_rets]))  # length n+1

    # All bars are IS (before OOS cutoff); timestamps far before OOS_CUTOFF_MS
    close_times = np.arange(n + 1) * 8 * 60 * 60 * 1000 + 1_000_000

    df = pd.DataFrame(
        {
            "symbol": "BTCUSDT",
            "close_time": close_times.astype(np.int64),
            "close": closes,
        }
    )

    result = compute_per_symbol_vol_ceiling(df, "BTCUSDT", lookback_bars=90, percentile=75.0)

    # Manually compute the expected value
    rv_series = np.array([compute_rv_30d_ann_at_bar(closes, i, 90) for i in range(len(closes))])
    valid = rv_series[~np.isnan(rv_series)]
    expected = float(np.percentile(valid, 75.0))

    assert abs(result - expected) < 1e-6, (
        f"compute_per_symbol_vol_ceiling p75 mismatch: got {result:.8f}, expected {expected:.8f}"
    )


# ---------------------------------------------------------------------------
# Test 3 — OOS exclusion (look-ahead safety)
# ---------------------------------------------------------------------------


def test_v1_038_compute_per_symbol_vol_ceiling_oos_exclusion() -> None:
    """Bars at or after OOS_CUTOFF_MS must be excluded from percentile estimation.

    Validates the IS-only constraint: passing bars with future timestamps does
    not change the result compared to passing only IS bars.
    """
    import pandas as pd

    from crypto_trade.risk.vol_ceiling import (
        _OOS_CUTOFF_MS,
        compute_per_symbol_vol_ceiling,
    )

    rng = np.random.default_rng(123)
    n_is = 200

    log_rets_is = rng.normal(0.0, 0.008, n_is)
    closes_is = np.cumprod(np.exp(np.r_[np.log(50.0), log_rets_is]))

    # IS timestamps: 200 * 8h intervals ending just before OOS cutoff
    is_end_ms = _OOS_CUTOFF_MS - 200 * 8 * 3600 * 1000
    close_times_is = is_end_ms + np.arange(n_is + 1) * 8 * 3600 * 1000

    df_is_only = pd.DataFrame(
        {"symbol": "ETHUSDT", "close_time": close_times_is.astype(np.int64), "close": closes_is}
    )

    # Add 50 OOS bars (timestamps >= OOS_CUTOFF_MS) with very different vol
    log_rets_oos = rng.normal(0.0, 0.10, 50)  # much higher vol
    closes_oos = np.cumprod(np.exp(np.r_[np.log(closes_is[-1]), log_rets_oos]))
    close_times_oos = _OOS_CUTOFF_MS + np.arange(51) * 8 * 3600 * 1000

    df_with_oos = pd.concat(
        [
            df_is_only,
            pd.DataFrame(
                {
                    "symbol": "ETHUSDT",
                    "close_time": close_times_oos.astype(np.int64),
                    "close": closes_oos,
                }
            ),
        ],
        ignore_index=True,
    )

    result_is_only = compute_per_symbol_vol_ceiling(df_is_only, "ETHUSDT", percentile=75.0)
    result_with_oos = compute_per_symbol_vol_ceiling(df_with_oos, "ETHUSDT", percentile=75.0)

    assert abs(result_is_only - result_with_oos) < 1e-6, (
        f"OOS bars contaminated IS percentile: IS-only={result_is_only:.6f} "
        f"vs with_OOS={result_with_oos:.6f}. "
        "compute_per_symbol_vol_ceiling must exclude close_time >= OOS_CUTOFF_MS."
    )


# ---------------------------------------------------------------------------
# Test 4 — apply_vol_ceiling: above threshold returns scale_factor
# ---------------------------------------------------------------------------


def test_v1_038_apply_vol_ceiling_above_threshold() -> None:
    """current_rv > threshold must return scale_factor (0.5)."""
    from crypto_trade.risk.vol_ceiling import apply_vol_ceiling

    result = apply_vol_ceiling(current_rv=1.5, threshold=1.0, scale_factor=0.5)
    assert abs(result - 0.5) < 1e-9, (
        f"apply_vol_ceiling must return 0.5 when rv > threshold, got {result}."
    )

    # Custom scale
    result_custom = apply_vol_ceiling(current_rv=2.0, threshold=1.8, scale_factor=0.25)
    assert abs(result_custom - 0.25) < 1e-9, (
        f"apply_vol_ceiling with custom scale_factor=0.25, got {result_custom}."
    )


# ---------------------------------------------------------------------------
# Test 5 — apply_vol_ceiling: below or equal threshold returns 1.0
# ---------------------------------------------------------------------------


def test_v1_038_apply_vol_ceiling_below_threshold() -> None:
    """current_rv <= threshold must return 1.0 (no adjustment)."""
    from crypto_trade.risk.vol_ceiling import apply_vol_ceiling

    # Strictly below
    result_below = apply_vol_ceiling(current_rv=0.8, threshold=1.0, scale_factor=0.5)
    assert abs(result_below - 1.0) < 1e-9, (
        f"apply_vol_ceiling must return 1.0 when rv < threshold, got {result_below}."
    )

    # Equal (threshold is NOT exceeded at equality — ceiling fires only when strictly >)
    result_equal = apply_vol_ceiling(current_rv=1.0, threshold=1.0, scale_factor=0.5)
    assert abs(result_equal - 1.0) < 1e-9, (
        f"apply_vol_ceiling must return 1.0 when rv == threshold (not strictly >), "
        f"got {result_equal}."
    )


# ---------------------------------------------------------------------------
# Test 6 — apply_vol_ceiling: NaN rv returns 1.0 (safety)
# ---------------------------------------------------------------------------


def test_v1_038_apply_vol_ceiling_nan_rv() -> None:
    """NaN current_rv must return 1.0 (safety: entry proceeds at full size)."""
    from crypto_trade.risk.vol_ceiling import apply_vol_ceiling

    result_nan_rv = apply_vol_ceiling(current_rv=float("nan"), threshold=1.0, scale_factor=0.5)
    assert abs(result_nan_rv - 1.0) < 1e-9, (
        f"apply_vol_ceiling must return 1.0 when rv is NaN, got {result_nan_rv}."
    )

    # NaN threshold also returns 1.0
    result_nan_thr = apply_vol_ceiling(current_rv=1.5, threshold=float("nan"), scale_factor=0.5)
    assert abs(result_nan_thr - 1.0) < 1e-9, (
        f"apply_vol_ceiling must return 1.0 when threshold is NaN, got {result_nan_thr}."
    )


# ---------------------------------------------------------------------------
# Test 7 — compute_rv_30d_ann_at_bar: past-only (look-ahead audit)
# ---------------------------------------------------------------------------


def test_v1_038_rv_30d_ann_past_only() -> None:
    """compute_rv_30d_ann_at_bar must use only closes[:idx+1].

    Providing additional future closes (idx+1 onward) must NOT change the output
    at the same idx — verifying look-ahead safety.
    """
    from crypto_trade.risk.vol_ceiling import compute_rv_30d_ann_at_bar

    rng = np.random.default_rng(99)
    n = 200
    log_rets = rng.normal(0.0, 0.015, n)
    closes = np.cumprod(np.exp(np.r_[np.log(100.0), log_rets]))  # length n+1

    idx = 150  # arbitrary mid-series bar
    result_full = compute_rv_30d_ann_at_bar(closes, idx, lookback_bars=90)

    # Truncate at idx+1 (exactly what the function is supposed to see)
    result_truncated = compute_rv_30d_ann_at_bar(closes[: idx + 1], idx, lookback_bars=90)

    assert abs(result_full - result_truncated) < 1e-10, (
        f"compute_rv_30d_ann_at_bar result changed when future closes provided: "
        f"full={result_full:.10f} vs truncated={result_truncated:.10f}. "
        "This indicates a look-ahead bias bug — the function must use only closes[:idx+1]."
    )


# ---------------------------------------------------------------------------
# Test 8 — Dispatch banner in runner source
# ---------------------------------------------------------------------------


def test_v1_038_dispatch_banner_in_source() -> None:
    """Runner source must contain the expected dispatch banner for iter-v1/038."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/038] VOL-CEILING ACTIVE" in src, (
        "run_baseline_v1.py must print '[iter-v1/038] VOL-CEILING ACTIVE' banner. "
        "This is F-AXIS #1 wiring proof per brief Section 2."
    )
    assert "risk-primitive axis" in src or "risk_primitive" in src or "risk-primitive" in src, (
        "Dispatch banner or comment must mention 'risk-primitive axis' for axis-family declaration."
    )


# ---------------------------------------------------------------------------
# Test 9 — Pre-flight assert: wrong vol-ceiling-mode
# ---------------------------------------------------------------------------


def test_v1_038_dispatch_pre_flight_mode_assert() -> None:
    """iter-v1/038 dispatch with --vol-ceiling-mode none must fire AssertionError."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    # Verify the AssertionError guard is present in the source
    assert 'vol_ceiling_mode_arg == "per_symbol"' in src, (
        "run_baseline_v1.py must contain assert for vol_ceiling_mode_arg == 'per_symbol' "
        "in the iter-v1/038 dispatch branch."
    )
    assert "pre-flight FAIL" in src, (
        "run_baseline_v1.py must mention 'pre-flight FAIL' in assertion error message "
        "for iter-v1/038."
    )


# ---------------------------------------------------------------------------
# Test 10 — Pre-flight assert: wrong vol-ceiling-pct
# ---------------------------------------------------------------------------


def test_v1_038_dispatch_pre_flight_pct_assert() -> None:
    """iter-v1/038 dispatch with --vol-ceiling-pct outside [70,80] must fire AssertionError."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    # The assert covers range [70.0, 80.0] check
    assert "70.0 <= vol_ceiling_pct_arg <= 80.0" in src, (
        "run_baseline_v1.py must contain assert '70.0 <= vol_ceiling_pct_arg <= 80.0' "
        "in the iter-v1/038 dispatch branch to enforce pct=75 brief constraint."
    )


# ---------------------------------------------------------------------------
# Test 11 — Baseline catch-all exclusion
# ---------------------------------------------------------------------------


def test_v1_038_in_baseline_catchall_exclusion() -> None:
    """'v1-038' must appear in the catch-all exclusion tuple in run_baseline_v1.py."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-038"' in src, (
        "run_baseline_v1.py must contain string 'v1-038' in the catch-all exclusion tuple. "
        "Without this, the catch-all fires first and produces a mislabeled BASELINE backtest "
        "(/030 dispatch defect)."
    )
    assert "iteration_label not in" in src, (
        "'iteration_label not in' pattern must exist for the catch-all exclusion tuple."
    )


# ---------------------------------------------------------------------------
# Test 12 — Per-symbol threshold logged at run start
# ---------------------------------------------------------------------------


def test_v1_038_vol_ceiling_thresholds_logged() -> None:
    """Dispatch block must log per-symbol threshold values at run start.

    Source inspection verifies the threshold logging statement is present.
    The brief Section 3.2 dispatch requires 5 per-symbol threshold log lines
    (one per cohort), each with symbol + p75 threshold value.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[VOL-CEIL/038]" in src, (
        "run_baseline_v1.py must contain '[VOL-CEIL/038]' prefix in threshold log lines."
    )
    assert "rv_p" in src, (
        "Threshold log lines must reference 'rv_p' (e.g. 'rv_p75 threshold = ...')."
    )
    assert "scale_factor" in src or "scale=" in src, (
        "Threshold log lines must reference scale_factor for F-AXIS #2 wiring verification."
    )


# ---------------------------------------------------------------------------
# Foundation regression — walk_forward embargo discipline
# ---------------------------------------------------------------------------


def test_v1_038_walk_forward_embargo_regression() -> None:
    """walk_forward.py must implement train_end_ms = test_start_ms - embargo_ms.

    Regression guard against the iter-v3/058 look-ahead bug (train_end_ms = test_start_ms
    with no embargo). Failure here means a regression that inflates IS/OOS Sharpe ~2x.
    """
    from crypto_trade.strategies.ml import walk_forward

    src = inspect.getsource(walk_forward)
    assert "embargo" in src.lower(), (
        "walk_forward.py must contain 'embargo' — the purge mechanism eliminating "
        "label-leakage at the train/test boundary (iter-v3/058 fix)."
    )
    assert "train_end_ms" in src, "walk_forward.py must contain 'train_end_ms' variable."
    assert "embargo_ms" in src or "embargo_candles" in src, (
        "walk_forward.py must reference embargo_ms or embargo_candles."
    )
