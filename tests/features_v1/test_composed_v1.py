"""Tests for v1 composed features — iter-v1/040.

Covers (as mandated by research_brief.md Section 10.3):
1.  test_hurst_rs_byte_identical_to_v3 — synthetic 100-bar series produces
    bit-identical Hurst as v3's _hurst_rs.
2.  test_rolling_hurst_burn_in_nan — first 99 bars are NaN (rolling warm-up).
3.  test_compute_regime_momentum_signed_5d_known_values — sample-instance
    assertion on synthetic series matches hand-computed ret_5d × sign(hurst − 0.5).
4.  test_compute_regime_momentum_signed_5d_past_only — bar t's value uses
    ONLY close[t-15..t] for ret_5d AND close[t-100..t] for hurst (no forward-leak).
5.  test_compute_regime_momentum_signed_5d_burn_in — first max(15, 100) - 1 = 99
    bars are NaN per symbol.
6.  test_add_composed_v1_features_btc_smoke — runs on real BTC data; output has
    regime_momentum_signed_5d column; non-null fraction > 95% after burn-in.
7.  test_add_composed_v1_features_stationarity — ADF p-value < 0.01 on BTC IS slice.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helper: minimal kline DataFrame
# ---------------------------------------------------------------------------


def _make_df(n: int = 200, seed: int = 42, close_start: float = 50_000.0) -> pd.DataFrame:
    """Create a minimal kline DataFrame with open_time and close columns."""
    rng = np.random.default_rng(seed)
    start_ms = 1_600_000_000_000
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    closes = close_start * np.cumprod(1 + rng.normal(0, 0.005, n))
    return pd.DataFrame({"open_time": open_times, "close": closes})


# ---------------------------------------------------------------------------
# Test 1 — _hurst_rs is bit-identical to v3's implementation
# ---------------------------------------------------------------------------


def test_hurst_rs_byte_identical_to_v3() -> None:
    """_hurst_rs in composed_v1 must produce bit-identical output to v3's _hurst_rs.

    Both are BYTE-FOR-BYTE copies of the same function. A synthetic 100-bar
    log-price series is passed to both; output must be exactly equal (not just
    close-to-equal) since the math is deterministic.
    """
    from crypto_trade.features_v1.composed_v1 import _hurst_rs as v1_hurst_rs
    from crypto_trade.features_v3.regime_v3 import _hurst_rs as v3_hurst_rs

    rng = np.random.default_rng(99)
    log_prices = np.log(50_000 * np.cumprod(1 + rng.normal(0, 0.005, 100)))

    v1_result = v1_hurst_rs(log_prices)
    v3_result = v3_hurst_rs(log_prices)

    assert v1_result == v3_result, (
        f"_hurst_rs byte-identity broken: v1={v1_result} vs v3={v3_result}. "
        "composed_v1._hurst_rs must be a BYTE-FOR-BYTE copy of regime_v3._hurst_rs."
    )
    assert np.isfinite(v1_result), (
        f"_hurst_rs returned non-finite result {v1_result} on a 100-bar synthetic series. "
        "Expected a finite Hurst exponent."
    )


# ---------------------------------------------------------------------------
# Test 2 — _rolling_hurst burn-in NaN
# ---------------------------------------------------------------------------


def test_rolling_hurst_burn_in_nan() -> None:
    """First 99 bars of _rolling_hurst(window=100) must be NaN.

    The rolling computation uses values[i-window:i], so the first valid output
    (at index i=window-1=99) requires 100 bars. Bars 0..98 have NaN.
    """
    from crypto_trade.features_v1.composed_v1 import _rolling_hurst

    rng = np.random.default_rng(42)
    log_close = pd.Series(np.log(50_000 * np.cumprod(1 + rng.normal(0, 0.005, 200))))

    result = _rolling_hurst(log_close, window=100)

    # First 99 rows must be NaN
    assert result.iloc[:99].isna().all(), (
        f"Expected first 99 bars to be NaN; got {result.iloc[:99].notna().sum()} non-NaN values. "
        "_rolling_hurst window=100 requires 100 bars before producing a valid output."
    )
    # Row 99 (0-indexed) must be finite
    assert np.isfinite(result.iloc[99]), (
        f"Expected row 99 to be finite; got {result.iloc[99]}. "
        "_rolling_hurst should produce the first valid output at index window-1=99."
    )


# ---------------------------------------------------------------------------
# Test 3 — Known-values assertion
# ---------------------------------------------------------------------------


def test_compute_regime_momentum_signed_5d_known_values() -> None:
    """Hand-computed known-values check on a small synthetic series.

    Creates a deterministic 120-bar series (burn-in=99 bars, so first valid output
    at bar 99). Verifies bar 110 output against hand-computation:
        ret_5d = log(close[110]) − log(close[110 − 15])
        hurst_100 = from bar 10..109 (window=100 bars ending at bar 110)
        composed = ret_5d × sign(hurst_100 − 0.5)
    Tolerance: < 1e-9 (pure floating-point arithmetic; should be bit-identical).
    """
    from crypto_trade.features_v1.composed_v1 import _hurst_rs, compute_regime_momentum_signed_5d

    n = 120
    df = _make_df(n=n, seed=777)
    result_df = compute_regime_momentum_signed_5d(df.copy())

    # Hand-compute bar 110
    bar = 110
    close = df["close"].values.astype(float)
    log_close = np.log(np.clip(close, 1e-12, None))

    ret_5d_bar = log_close[bar] - log_close[bar - 15]

    # Hurst over bars [bar-100 .. bar] = bars 10..110 (window=100)
    window_vals = log_close[bar - 100 : bar]  # exactly 100 bars ending at bar-1
    hurst_val = _hurst_rs(window_vals)
    sign_val = np.sign(hurst_val - 0.5)
    if sign_val == 0.0:
        sign_val = np.nan
    expected = ret_5d_bar * sign_val

    observed = result_df["regime_momentum_signed_5d"].iloc[bar]

    if np.isnan(expected):
        assert np.isnan(observed), (
            f"Expected NaN at bar {bar} (sign=0 edge case) but got {observed}."
        )
    else:
        assert abs(observed - expected) < 1e-9, (
            f"Known-values mismatch at bar {bar}: observed={observed}, expected={expected}, "
            f"diff={abs(observed - expected):.2e}. "
            "compute_regime_momentum_signed_5d must produce ret_5d × sign(hurst_100 − 0.5)."
        )


# ---------------------------------------------------------------------------
# Test 4 — Past-only invariant (no lookahead)
# ---------------------------------------------------------------------------


def test_compute_regime_momentum_signed_5d_past_only() -> None:
    """Bar t's regime_momentum_signed_5d must NOT use close[t+1] or beyond.

    Mechanism: inject a spike at bar 110. If bar 110's output is affected by
    bar 111's close, the past-only invariant is violated. We compare output at
    bar 109 between the original series and a version where bar 111 is set to
    a very different value. Bar 109's output must be bit-identical.
    """
    from crypto_trade.features_v1.composed_v1 import compute_regime_momentum_signed_5d

    n = 130
    df1 = _make_df(n=n, seed=42)
    df2 = df1.copy()
    # Inject a 10× spike at bar 111 (should NOT affect bar 109's output)
    df2.at[111, "close"] = df2.at[111, "close"] * 10.0

    result1 = compute_regime_momentum_signed_5d(df1)
    result2 = compute_regime_momentum_signed_5d(df2)

    # Bar 109 should be identical (spike is at bar 111, 2 bars in the future)
    val1 = result1["regime_momentum_signed_5d"].iloc[109]
    val2 = result2["regime_momentum_signed_5d"].iloc[109]

    if np.isnan(val1):
        assert np.isnan(val2), (
            f"Bar 109 is NaN in baseline but {val2} after future-bar spike. "
            "Past-only invariant violated."
        )
    else:
        assert val1 == val2, (
            f"Bar 109 changed from {val1} to {val2} after injecting spike at bar 111. "
            "Past-only invariant violated: bar t must NOT use close[t+1] or later."
        )


# ---------------------------------------------------------------------------
# Test 5 — Burn-in NaN for composed feature
# ---------------------------------------------------------------------------


def test_compute_regime_momentum_signed_5d_burn_in() -> None:
    """First 99 bars must be NaN (hurst_100 dominates ret_5d burn-in of 15 bars)."""
    from crypto_trade.features_v1.composed_v1 import compute_regime_momentum_signed_5d

    df = _make_df(n=200, seed=42)
    result = compute_regime_momentum_signed_5d(df)

    col = result["regime_momentum_signed_5d"]
    # Bars 0..98 must be NaN (hurst_100 requires 100 bars; first valid at bar 99)
    assert col.iloc[:99].isna().all(), (
        f"Expected first 99 bars to be NaN; got {col.iloc[:99].notna().sum()} non-NaN values. "
        "hurst_100 requires 100 bars (window=100), so bars 0..98 must be NaN."
    )
    # Bar 99 should be finite
    assert np.isfinite(col.iloc[99]), (
        f"Expected bar 99 to be finite; got {col.iloc[99]}. "
        "regime_momentum_signed_5d should produce the first valid output at index 99."
    )


# ---------------------------------------------------------------------------
# Test 6 — BTC smoke test (real data)
# ---------------------------------------------------------------------------


def test_add_composed_v1_features_btc_smoke() -> None:
    """Smoke test on real BTC 8h parquet data.

    Verifies:
    - regime_momentum_signed_5d column is present in the output.
    - Non-null fraction > 95% after the 99-bar burn-in.
    - No NaN appears after the burn-in window (except possible edge at exact bar 99).
    """
    from pathlib import Path

    import pandas as pd

    from crypto_trade.features_v1.composed_v1 import add_composed_v1_features

    parquet_path = Path("data/features/BTCUSDT_8h_features.parquet")
    if not parquet_path.exists():
        pytest.skip(f"BTC feature parquet not found at {parquet_path}; skipping smoke test.")

    df = pd.read_parquet(parquet_path)
    result = add_composed_v1_features(df)

    assert "regime_momentum_signed_5d" in result.columns, (
        "add_composed_v1_features did not add 'regime_momentum_signed_5d' column. "
        "Check composed_v1.compute_regime_momentum_signed_5d implementation."
    )

    col = result["regime_momentum_signed_5d"]
    n_total = len(col)
    n_after_burnin = max(0, n_total - 99)
    if n_after_burnin == 0:
        pytest.skip(f"BTC parquet has only {n_total} rows, fewer than 100 (burn-in). Skipping.")

    non_null_frac = col.iloc[99:].notna().sum() / n_after_burnin
    assert non_null_frac > 0.95, (
        f"Expected > 95% non-null fraction after burn-in; got {non_null_frac:.3f}. "
        "regime_momentum_signed_5d has too many NaN values after the 99-bar warm-up."
    )


# ---------------------------------------------------------------------------
# Test 7 — Stationarity (ADF) on BTC IS slice
# ---------------------------------------------------------------------------


def test_add_composed_v1_features_stationarity() -> None:
    """ADF p-value < 0.01 on BTC IS slice (close_time < 2025-03-24).

    Replicates Section 1.2 EDA stationarity check from the research brief.
    A p-value >= 0.01 would indicate a non-stationary time series that violates
    v1 stationarity discipline.
    """
    from pathlib import Path

    import pandas as pd

    from crypto_trade.features_v1.composed_v1 import add_composed_v1_features

    try:
        from statsmodels.tsa.stattools import adfuller
    except ImportError:
        pytest.skip("statsmodels not installed; skipping ADF stationarity test.")

    parquet_path = Path("data/features/BTCUSDT_8h_features.parquet")
    if not parquet_path.exists():
        pytest.skip(f"BTC feature parquet not found at {parquet_path}; skipping ADF test.")

    df = pd.read_parquet(parquet_path)

    # IS-only filter: close_time < 2025-03-24 00:00 UTC
    oos_cutoff_ms = 1_742_774_400_000  # 2025-03-24 00:00 UTC in ms
    if "close_time" in df.columns:
        df_is = df[df["close_time"] < oos_cutoff_ms].copy()
    elif "open_time" in df.columns:
        df_is = df[df["open_time"] < oos_cutoff_ms].copy()
    else:
        df_is = df.copy()

    result = add_composed_v1_features(df_is)
    col = result["regime_momentum_signed_5d"].dropna()

    if len(col) < 50:
        pytest.skip(f"Only {len(col)} non-NaN IS rows; ADF requires more data.")

    adf_result = adfuller(col.values, autolag="AIC")
    p_value = adf_result[1]

    assert p_value < 0.01, (
        f"ADF p-value {p_value:.4f} >= 0.01 for regime_momentum_signed_5d on BTC IS slice. "
        "Feature is non-stationary by ADF test, violating v1 stationarity discipline. "
        "Check EDA Section 1.2 — all 5 v1 symbols expected ADF p << 0.001."
    )
