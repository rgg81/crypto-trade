"""Adversarial tests for compute_vol_normalized_ret_5d — iter-v3/048.

5 mandatory tests per brief Section 3 Sub-fix 5:

1. test_vol_normalized_ret_5d_past_only_discipline — verify the value at bar t
   depends only on rv at bar t and close at bars [t-15, t]; no future leakage.
2. test_vol_normalized_ret_5d_warmup_nan — first 15 bars NaN from ret_5d warmup;
   with synthetic rv available the warmup is determined by ret_5d (15 bars).
3. test_vol_normalized_ret_5d_zero_vol_protection — when rv == 0, the result is
   bounded (no inf/NaN cascade); epsilon=1e-6 prevents division by zero.
4. test_vol_normalized_ret_5d_monotonicity — when ret_5d > 0 and rv constant,
   the result monotonically increases with ret_5d magnitude.
5. test_vol_normalized_ret_5d_missing_input_returns_nan — when range_realized_vol_50
   is missing from input df, the column is added as all-NaN (graceful failure).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features_v3.engineered_v3 import compute_vol_normalized_ret_5d

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC


def _make_df_with_rv(
    n: int = 200,
    seed: int = 42,
    close_values: np.ndarray | None = None,
    rv_values: np.ndarray | None = None,
) -> pd.DataFrame:
    """Create a minimal DataFrame with close and range_realized_vol_50 columns.

    Args:
        n: number of rows.
        seed: numpy rng seed.
        close_values: optional override for close column (length must == n).
        rv_values: optional override for range_realized_vol_50 column (length == n).
    """
    rng = np.random.default_rng(seed)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    if close_values is None:
        close = rng.uniform(100.0, 1000.0, n)
    else:
        close = np.asarray(close_values, dtype=float)
    if rv_values is None:
        rv = rng.uniform(0.001, 0.05, n)
    else:
        rv = np.asarray(rv_values, dtype=float)
    return pd.DataFrame(
        {
            "open_time": open_times,
            "close": close,
            "range_realized_vol_50": rv,
        }
    )


# ---------------------------------------------------------------------------
# Test 1: past-only discipline
# ---------------------------------------------------------------------------


def test_vol_normalized_ret_5d_past_only_discipline() -> None:
    """Appending a future bar must NOT alter the value at any existing bar t.

    Methodology: compute the feature on n rows, then append one row with a
    very different close value and recompute. The first n values must be
    identical to within floating-point precision.
    """
    n = 100
    rng = np.random.default_rng(77)
    close = rng.uniform(100.0, 1000.0, n)
    rv = rng.uniform(0.001, 0.05, n)
    df_short = _make_df_with_rv(n=n, close_values=close, rv_values=rv)

    # Append one "future" bar with extreme close and rv
    future_close = np.append(close, 1e9)  # wildly different value
    future_rv = np.append(rv, 0.0001)
    df_long = _make_df_with_rv(n=n + 1, close_values=future_close, rv_values=future_rv)

    result_short = compute_vol_normalized_ret_5d(df_short)["vol_normalized_ret_5d"].values
    result_long = compute_vol_normalized_ret_5d(df_long)["vol_normalized_ret_5d"].values

    # The first n values must be identical (ignoring NaN positions)
    for i in range(n):
        v_short = result_short[i]
        v_long = result_long[i]
        if np.isnan(v_short):
            assert np.isnan(v_long), (
                f"Bar {i}: was NaN in short run but {v_long} in long run — "
                "future bar should not introduce non-NaN value at warmup position."
            )
        else:
            assert np.isclose(v_short, v_long, rtol=1e-10, atol=0), (
                f"Bar {i}: past-only violation. short={v_short}, long={v_long}. "
                "Appending a future bar must not alter prior bar values."
            )


# ---------------------------------------------------------------------------
# Test 2: warmup NaN
# ---------------------------------------------------------------------------


def test_vol_normalized_ret_5d_warmup_nan() -> None:
    """First 15 bars must be NaN (ret_5d requires close.shift(15); bars 0..14 lack history).

    With synthetic rv available from bar 0 (no RV warmup imposed), the warmup
    is determined by ret_5d's shift(15) requirement: log_close[t] - log_close[t-15].
    Bars 0..14 have no log_close[t-15], so ret_5d is NaN there, making vol_normalized_ret_5d
    NaN for bars 0..14.

    Bars 15+ (with finite rv) should be non-NaN.
    """
    n = 100
    rng = np.random.default_rng(13)
    close = rng.uniform(100.0, 1000.0, n)
    # Use a constant, positive rv so rv is never NaN
    rv = np.full(n, 0.01)
    df = _make_df_with_rv(n=n, close_values=close, rv_values=rv)

    result = compute_vol_normalized_ret_5d(df)["vol_normalized_ret_5d"]

    # First 15 bars must be NaN (ret_5d warmup dominates)
    assert result.iloc[:15].isna().all(), (
        f"Expected first 15 bars to be NaN (ret_5d warmup). Got: {result.iloc[:15].values}"
    )

    # Bars 15+ should be non-NaN when close and rv are valid
    assert result.iloc[15:].notna().all(), (
        f"Expected bars 15+ to be non-NaN with valid close and rv. "
        f"First few non-NaN values: {result.iloc[15:20].values}"
    )


# ---------------------------------------------------------------------------
# Test 3: zero vol protection (epsilon guard)
# ---------------------------------------------------------------------------


def test_vol_normalized_ret_5d_zero_vol_protection() -> None:
    """When range_realized_vol_50 == 0.0, the output must be finite (not inf or NaN).

    The epsilon=1e-6 in the denominator prevents division by zero. The result
    should be ret_5d / 1e-6, which is a large but finite number.
    """
    n = 100
    # Use monotonically increasing close so ret_5d is always positive and well-defined
    close = np.cumprod(np.ones(n) * 1.001) * 100.0
    # All rv == 0.0 — epsilon must save us
    rv = np.zeros(n)
    df = _make_df_with_rv(n=n, close_values=close, rv_values=rv)

    result = compute_vol_normalized_ret_5d(df)["vol_normalized_ret_5d"]

    # No bar should be NaN or inf after warmup
    valid = result.iloc[15:]
    assert not valid.isna().any(), (
        f"Got NaN despite epsilon guard on zero rv: {valid[valid.isna()].index.tolist()}"
    )
    assert not np.isinf(valid.values).any(), (
        f"Got inf despite epsilon guard on zero rv: {valid[np.isinf(valid.values)].index.tolist()}"
    )

    # The magnitude should be ret_5d / 1e-6 — verify it's large but finite
    max_abs = valid.abs().max()
    assert max_abs < 1e9, (
        f"Value magnitude {max_abs} implausibly large even with epsilon guard. "
        "Check epsilon = 1e-6 guard in compute_vol_normalized_ret_5d."
    )
    # Must be nonzero (since ret_5d != 0 with trending close)
    assert max_abs > 0, "Expected nonzero output with zero rv and trending close."


# ---------------------------------------------------------------------------
# Test 4: monotonicity
# ---------------------------------------------------------------------------


def test_vol_normalized_ret_5d_monotonicity() -> None:
    """When ret_5d > 0 and rv is constant, the result monotonically increases with ret_5d.

    Construct two scenarios:
    - Scenario slow: close rises slowly over 15 bars (small ret_5d > 0).
    - Scenario fast: close rises quickly over 15 bars (larger ret_5d > 0).
    With rv constant and positive, vol_normalized_ret_5d_fast > vol_normalized_ret_5d_slow
    at bar 15+.
    """
    n = 50
    rv_const = 0.01

    # Scenario slow: slow uptrend (1% per bar over 15 bars ~ +15% ret_5d)
    close_slow = np.ones(n) * 100.0
    for i in range(1, n):
        close_slow[i] = close_slow[i - 1] * 1.01
    rv_slow = np.full(n, rv_const)
    df_slow = _make_df_with_rv(n=n, close_values=close_slow, rv_values=rv_slow)
    result_slow = compute_vol_normalized_ret_5d(df_slow)["vol_normalized_ret_5d"]

    # Scenario fast: fast uptrend (3% per bar over 15 bars ~ +57% ret_5d)
    close_fast = np.ones(n) * 100.0
    for i in range(1, n):
        close_fast[i] = close_fast[i - 1] * 1.03
    rv_fast = np.full(n, rv_const)
    df_fast = _make_df_with_rv(n=n, close_values=close_fast, rv_values=rv_fast)
    result_fast = compute_vol_normalized_ret_5d(df_fast)["vol_normalized_ret_5d"]

    # At bar 15 (first non-NaN), fast must exceed slow
    val_slow_15 = result_slow.iloc[15]
    val_fast_15 = result_fast.iloc[15]

    assert not np.isnan(val_slow_15), "Slow scenario bar 15 is NaN — check ret_5d warmup."
    assert not np.isnan(val_fast_15), "Fast scenario bar 15 is NaN — check ret_5d warmup."
    assert val_slow_15 > 0, (
        f"Slow uptrend should produce positive vol_normalized_ret_5d at bar 15. Got: {val_slow_15}"
    )
    assert val_fast_15 > val_slow_15, (
        f"Monotonicity violation: slow={val_slow_15} >= fast={val_fast_15} "
        "with constant rv. Larger ret_5d must produce larger vol_normalized_ret_5d."
    )


# ---------------------------------------------------------------------------
# Test 5: missing input returns NaN (graceful failure)
# ---------------------------------------------------------------------------


def test_vol_normalized_ret_5d_missing_input_returns_nan() -> None:
    """When range_realized_vol_50 is missing from input df, the column is all-NaN.

    The function must not raise an error. It must return a copy of the df with
    vol_normalized_ret_5d added as all-NaN. This allows the downstream runner's
    _verify_feature_columns assertion to catch the gap explicitly.
    """
    n = 100
    rng = np.random.default_rng(99)
    close = rng.uniform(100.0, 1000.0, n)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    # Deliberately omit range_realized_vol_50
    df = pd.DataFrame({"open_time": open_times, "close": close})

    result = compute_vol_normalized_ret_5d(df)

    assert "vol_normalized_ret_5d" in result.columns, (
        "vol_normalized_ret_5d column must be added even when range_realized_vol_50 is missing."
    )
    assert result["vol_normalized_ret_5d"].isna().all(), (
        "vol_normalized_ret_5d must be all-NaN when range_realized_vol_50 is missing. "
        f"Got non-NaN at: {result.index[result['vol_normalized_ret_5d'].notna()].tolist()}"
    )
    # Original columns must be preserved
    assert "open_time" in result.columns
    assert "close" in result.columns
    # range_realized_vol_50 must NOT be added (graceful passthrough of missing column)
    assert "range_realized_vol_50" not in result.columns, (
        "Function must not invent range_realized_vol_50 when it is absent from input."
    )
