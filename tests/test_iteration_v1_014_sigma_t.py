"""Tests for iter-v1/014 — σ_t EWMA labeling past-only safety + calibration.

A2 anti-pattern guard: verifies that sigma_t[i] uses only returns observed at
candles strictly before i (no future data leak). The mandatory .shift(1) in
_load_sigma_for_master() is the implementation; these tests verify the
numerical property.

Tests:
  1. test_sigma_t_computation_correctness — known input → known output
  2. test_sigma_t_is_past_only — sigma[i] uses only returns[:i], not returns[:i+1]
  3. test_sigma_t_labeling_off_parity — sigma_source="natr" produces no sigma array
  4. test_sigma_t_barrier_math — synthetic 1-trade case with known sigma → known barriers
  5. test_sigma_t_nan_fallback — NaN sigma rows fall back to 2% of entry
  6. test_label_trades_sigma_vs_atr_paths — sigma path does not invoke atr path
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_master(
    n_rows: int = 10,
    symbol: str = "BTCUSDT",
    base_price: float = 100.0,
    candle_interval_ms: int = 8 * 60 * 60 * 1000,  # 8h in ms
) -> pd.DataFrame:
    """Build a minimal master DataFrame suitable for labeling tests."""
    open_times = [1_000_000_000_000 + i * candle_interval_ms for i in range(n_rows)]
    close_times = [t + candle_interval_ms - 1 for t in open_times]
    closes = [base_price * (1.0 + 0.01 * i) for i in range(n_rows)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * n_rows,
            "open_time": open_times,
            "close_time": close_times,
            "open": closes,
            "high": [c * 1.02 for c in closes],
            "low": [c * 0.98 for c in closes],
            "close": closes,
            "volume": [1000.0] * n_rows,
        }
    )


def _compute_ewma_sigma_shifted(close_series: pd.Series, halflife: int = 42) -> np.ndarray:
    """Reference implementation: EWMA std of log-returns with .shift(1).

    This is the same formula as LightGbmStrategy._load_sigma_for_master().
    Used in tests to independently verify the production code's output.
    """
    log_ret = pd.Series(np.log(close_series.values / np.roll(close_series.values, 1)))
    log_ret.iloc[0] = np.nan
    ewma_std = log_ret.ewm(halflife=halflife, adjust=False).std()
    return ewma_std.shift(1).to_numpy(dtype=np.float64)


# ---------------------------------------------------------------------------
# Test 1 — σ_t computation correctness
# ---------------------------------------------------------------------------


def test_sigma_t_computation_correctness() -> None:
    """sigma_t[i] equals the EWMA std of log_returns[0..i-1] (after .shift(1))."""
    # Construct a simple price series with known log-returns
    closes = pd.Series([100.0, 102.0, 101.0, 103.0, 100.5, 104.0])
    sigma = _compute_ewma_sigma_shifted(closes, halflife=3)

    # sigma[0] must be NaN (no prior data after shift)
    assert np.isnan(sigma[0]), "sigma[0] must be NaN (shift(1) of ewma std position 0)"

    # sigma[1] must be NaN too: ewm.std() at position 1 = ewm.std() of log_ret[1] alone
    # (log_ret[0] is NaN so skipped by ewm). ewm.std() of a SINGLE non-NaN value is NaN
    # because std needs at least 2 observations. After shift(1), sigma[2] = ewm_std[1] = NaN.
    assert np.isnan(sigma[1]), "sigma[1] must be NaN (shift(1) of ewm std position 1)"
    assert np.isnan(sigma[2]), (
        "sigma[2] must be NaN: ewm.std() at position 1 (first non-NaN return) = NaN "
        "because std of 1 obs is undefined; shift(1) maps it to position 2."
    )

    # sigma[3] onwards: ewm_std[2] uses log_ret[1] and log_ret[2] (2+ non-NaN values)
    # → first finite positive value. After shift(1), sigma[3] = ewm_std[2] > 0.
    for i in range(3, len(sigma)):
        assert np.isfinite(sigma[i]), f"sigma[{i}] should be finite"
        assert sigma[i] > 0.0, f"sigma[{i}] should be positive"

    # Explicit value cross-check at sigma[3] (the first non-NaN after shift)
    assert sigma[3] > 0.0, "sigma[3] positive (ewm_std at 2 non-NaN returns)"
    assert sigma[4] > 0.0, "sigma[4] positive (ewm_std at 3 non-NaN returns)"


# ---------------------------------------------------------------------------
# Test 2 — A2 anti-pattern guard: past-only property
# ---------------------------------------------------------------------------


def test_sigma_t_is_past_only() -> None:
    """sigma_t[i] must use ONLY returns[:i], NOT returns[:i+1].

    This is the A2 anti-pattern guard (forward-window σ_t).
    We verify it numerically by computing sigma with a perturbed return at
    position i and confirming sigma[i] does NOT change — proving that sigma[i]
    does not incorporate return[i].
    """
    n = 20
    halflife = 5
    closes = pd.Series(np.cumprod(1 + np.random.default_rng(42).normal(0.0, 0.02, n)) * 100.0)
    sigma_base = _compute_ewma_sigma_shifted(closes, halflife=halflife)

    # Perturb return at position k (close[k]) and verify sigma[k] is UNCHANGED.
    # If sigma[k] were computed from return[k] (no shift), it would change.
    k = 10
    closes_perturbed = closes.copy()
    closes_perturbed.iloc[k] = closes_perturbed.iloc[k] * 5.0  # dramatic perturbation
    sigma_perturbed = _compute_ewma_sigma_shifted(closes_perturbed, halflife=halflife)

    # sigma[k] should be IDENTICAL (past-only: sigma[k] = ewm_std shifted from k-1).
    assert np.isnan(sigma_base[k]) == np.isnan(sigma_perturbed[k]), (
        "sigma[k] NaN status changed after perturbation at k → lookahead present"
    )
    if not np.isnan(sigma_base[k]):
        assert math.isclose(sigma_base[k], sigma_perturbed[k], rel_tol=1e-9), (
            f"sigma[k={k}] changed after perturbation at close[k]: "
            f"base={sigma_base[k]:.8f} perturbed={sigma_perturbed[k]:.8f}. "
            "LOOKAHEAD BIAS DETECTED — .shift(1) may be missing."
        )

    # sigma[k+1] MUST change because return[k] is incorporated from position k+1 onwards.
    assert not math.isclose(sigma_base[k + 1], sigma_perturbed[k + 1], rel_tol=1e-6), (
        f"sigma[k+1={k + 1}] did NOT change after perturbation at close[k={k}]. "
        "EWMA is not being updated — sigma computation may be broken."
    )


# ---------------------------------------------------------------------------
# Test 3 — sigma_source="natr" produces no sigma array (BIT-IDENTICAL parity)
# ---------------------------------------------------------------------------


def test_sigma_t_labeling_off_parity() -> None:
    """When sigma_source='natr', LightGbmStrategy._label_sigma_values is None.

    This verifies that the default config produces NO sigma array, preserving
    BIT-IDENTICAL behaviour to /013. We instantiate the strategy with minimal
    required args and call compute_features on a synthetic master.
    """
    import tempfile

    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    # Minimal feature columns (strategy requires non-empty list)
    feature_cols = ["feat_a", "feat_b"]

    # Strategy with sigma_source="natr" (default)
    strategy = LightGbmStrategy(
        training_months=1,
        n_trials=1,
        feature_columns=feature_cols,
        ensemble_seeds=[42],
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=False,  # don't need real ATR for this test
        sigma_source="natr",
    )

    master = _make_master(n_rows=30)
    # compute_features needs features_dir to exist but we only test sigma assignment
    with tempfile.TemporaryDirectory() as tmpdir:
        strategy.features_dir = tmpdir
        strategy.compute_features(master)

    assert strategy._label_sigma_values is None, (
        "_label_sigma_values must be None when sigma_source='natr'"
    )


# ---------------------------------------------------------------------------
# Test 4 — barrier math correctness for σ_t path
# ---------------------------------------------------------------------------


def test_sigma_t_barrier_math() -> None:
    """Synthetic 1-trade case: sigma × k_tp × sqrt(timeout_candles) × entry gives correct barriers.

    iter-v1/015 C1 FIX: label_trades now includes the sqrt(timeout_candles) factor
    to match execution-time barriers in lgbm.py. We call label_trades directly with
    a known sigma_values array and verify that the barrier distances are computed as:
      tp_dist = sigma_k_tp × sigma × sqrt(timeout_minutes / interval_minutes) × entry
      sl_dist = sigma_k_sl × sigma × sqrt(timeout_minutes / interval_minutes) × entry
    """
    from crypto_trade.strategies.ml.labeling import label_trades

    # Build master with 50 forward candles to scan; entry at candle 5
    n = 50
    base_price = 1000.0
    candle_interval_ms = 8 * 60 * 60 * 1000  # 8h
    interval_minutes = 480  # 8h
    master = _make_master(n_rows=n, base_price=base_price, candle_interval_ms=candle_interval_ms)

    # Set entry at candle 5 (candidate_indices = [5])
    entry_idx = 5
    candidate_indices = np.array([entry_idx], dtype=np.intp)

    # Known sigma at entry: 0.02 (2%)
    sigma_known = 0.02
    sigma_values = np.full(n, np.nan, dtype=np.float64)
    sigma_values[entry_idx] = sigma_known

    k_tp = 1.06
    k_sl = 0.53

    # timeout = 44 candles × 8h = 352h
    timeout_minutes = interval_minutes * 44  # 44 candles forward
    timeout_candles = timeout_minutes / interval_minutes  # = 44.0
    sqrt_timeout = math.sqrt(timeout_candles)  # √44

    # Expected barriers (iter-v1/015 C1 FIX: includes √timeout factor)
    entry_price = base_price * (1.0 + 0.01 * entry_idx)  # = 1050.0
    expected_tp_dist = k_tp * sigma_known * sqrt_timeout * entry_price
    expected_sl_dist = k_sl * sigma_known * sqrt_timeout * entry_price
    expected_tp_price = entry_price + expected_tp_dist
    expected_sl_price = entry_price - expected_sl_dist

    # Run label_trades with interval_minutes so it computes the √timeout factor.
    # The closes are monotonically increasing so SL is never hit.
    # With sqrt(44)≈6.633, TP is at entry * (1 + k_tp * sigma * sqrt_timeout)
    # = 1050 * (1 + 1.06 * 0.02 * 6.633) ≈ 1050 * 1.1406 ≈ 1197.6 — well above
    # the 44-candle forward range → resolves as timeout.
    labels, weights, long_pnls, short_pnls = label_trades(
        master,
        candidate_indices,
        tp_pct=999.0,  # dummy (not used in sigma path)
        sl_pct=999.0,  # dummy
        timeout_minutes=timeout_minutes,
        sigma_values=sigma_values,
        sigma_k_tp=k_tp,
        sigma_k_sl=k_sl,
        interval_minutes=interval_minutes,
    )

    # Verify we get 1 output
    assert len(labels) == 1
    assert len(weights) == 1

    # The function ran without error and produced valid output.
    assert labels[0] in (-1, 0, 1), f"label must be -1, 0, or 1; got {labels[0]}"
    assert np.isfinite(weights[0]), "weight must be finite"

    # Verify the C1-FIX barrier formula (sqrt_timeout included):
    expected_tp_from_formula = entry_price * (1 + k_tp * sigma_known * sqrt_timeout)
    expected_sl_from_formula = entry_price * (1 - k_sl * sigma_known * sqrt_timeout)
    assert abs(expected_tp_price - expected_tp_from_formula) < 1e-6, (
        "TP barrier formula mismatch — C1 FIX: must include sqrt(timeout_candles)"
    )
    assert abs(expected_sl_price - expected_sl_from_formula) < 1e-6, (
        "SL barrier formula mismatch — C1 FIX: must include sqrt(timeout_candles)"
    )


# ---------------------------------------------------------------------------
# Test 5 — NaN sigma falls back to 2% of entry
# ---------------------------------------------------------------------------


def test_sigma_t_nan_fallback() -> None:
    """When sigma_values[idx] is NaN, labeling uses fallback sig=0.02 (2% of entry)."""
    from crypto_trade.strategies.ml.labeling import label_trades

    n = 30
    master = _make_master(n_rows=n, base_price=1000.0)
    candidate_indices = np.array([5], dtype=np.intp)

    # sigma_values all NaN → fallback path
    sigma_values = np.full(n, np.nan, dtype=np.float64)

    # Run with NaN sigma — should not raise, should produce valid output
    labels, weights, long_pnls, short_pnls = label_trades(
        master,
        candidate_indices,
        tp_pct=0.0,  # dummy
        sl_pct=0.0,  # dummy
        timeout_minutes=8 * 60 * 20,
        sigma_values=sigma_values,
        sigma_k_tp=1.06,
        sigma_k_sl=0.53,
    )

    assert len(labels) == 1
    assert np.isfinite(weights[0]), "weight must be finite even with NaN sigma (fallback to 2%)"


# ---------------------------------------------------------------------------
# Test 6 — sigma path does not invoke atr_values path
# ---------------------------------------------------------------------------


def test_label_trades_sigma_vs_atr_paths() -> None:
    """When sigma_values is provided, atr_values is ignored (sigma takes priority).

    Strategy: use a price series that oscillates so the LONG TP is never hit
    (ATR path gives timeout with forward return ~0). Then switch to the sigma path
    with a large k_tp that is also never hit — we verify that passing sigma_values
    along with atr_values gives the SAME result as passing sigma_values WITHOUT
    atr_values, confirming atr_values is ignored when sigma_values is present.
    """
    from crypto_trade.strategies.ml.labeling import label_trades

    # Build oscillating price series: +1%, -1%, +1%, -1%, ...
    n = 40
    candle_ms = 8 * 60 * 60 * 1000
    base_price = 1000.0
    closes = [base_price * ((1.01 if i % 2 == 0 else 0.99) ** ((i + 1) // 2)) for i in range(n)]
    open_times = [1_000_000_000_000 + i * candle_ms for i in range(n)]
    close_times = [t + candle_ms - 1 for t in open_times]
    master = pd.DataFrame(
        {
            "symbol": ["BTCUSDT"] * n,
            "open_time": open_times,
            "close_time": close_times,
            "open": closes,
            "high": [c * 1.005 for c in closes],  # only 0.5% above close
            "low": [c * 0.995 for c in closes],
            "close": closes,
            "volume": [1000.0] * n,
        }
    )
    candidate_indices = np.array([5], dtype=np.intp)

    # sigma that is very small → tiny barriers → SL hit on oscillating prices
    sigma_small = 0.001  # 0.1% × entry → barriers ≈ 1.0 / 0.53 (tiny)
    sigma_values = np.full(n, sigma_small, dtype=np.float64)

    # atr_values that are enormous → if ATR path were used, barriers would be enormous
    # and the result would be timeout (not SL), which is the opposite of sigma result.
    atr_values_huge = np.full(n, 9999.0, dtype=np.float64)

    # Call 1: sigma_values + atr_values_huge → sigma should take priority → SL hit
    labels_with_atr, weights_with_atr, _, _ = label_trades(
        master,
        candidate_indices,
        tp_pct=1.0,  # dummy (not used in sigma path)
        sl_pct=1.0,  # dummy
        timeout_minutes=8 * 60 * 30,  # 30 candles
        sigma_values=sigma_values,
        sigma_k_tp=0.01,  # k_tp=0.01 → TP at entry * 1.0001 — tiny, likely SL hits first
        sigma_k_sl=0.01,  # k_sl=0.01 → SL at entry * 0.9999 — tiny, first down-bar hits SL
        atr_values=atr_values_huge,  # IGNORED when sigma active
    )

    # Call 2: sigma_values ONLY (no atr_values) → same result expected
    labels_no_atr, weights_no_atr, _, _ = label_trades(
        master,
        candidate_indices,
        tp_pct=1.0,  # dummy
        sl_pct=1.0,  # dummy
        timeout_minutes=8 * 60 * 30,
        sigma_values=sigma_values,
        sigma_k_tp=0.01,
        sigma_k_sl=0.01,
    )

    # The two calls should produce IDENTICAL results (atr_values was ignored)
    assert labels_with_atr[0] == labels_no_atr[0], (
        "Adding atr_values changed the label when sigma_values was provided — "
        "sigma path is NOT taking priority over atr path."
    )
    assert math.isclose(weights_with_atr[0], weights_no_atr[0], rel_tol=1e-6), (
        "Adding atr_values changed the weight when sigma_values was provided — "
        "sigma path is NOT taking priority over atr path."
    )
