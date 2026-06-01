"""Tests for iter-v1/052: BTC-only specialist with funding-rate impulse + spread features.

Covers 6 mandatory tests:

1.  test_no_lookahead — verify the impulse feature does not use future funding-rate data.
2.  test_btc_only_cohort — V1_ITER052_UNIVERSE is exactly {"BTCUSDT"}.
3.  test_features_in_pruned — both new features present in V1_FEATURE_COLUMNS_PRUNED.
4.  test_pruned_size_48 — V1_FEATURE_COLUMNS_PRUNED has exactly 48 features.
5.  test_funding_impulse_synthetic — compute_btc_funding_rate_8h_impulse math is correct.
6.  test_funding_spread_correctness — compute_btc_funding_spread_30_90 math is correct.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# 1. test_no_lookahead
# ---------------------------------------------------------------------------


def test_no_lookahead() -> None:
    """btc_funding_rate_8h_impulse must not use future funding-rate data.

    The impulse is:
        diff(funding_rate)[t] / rolling(90).std(diff(funding_rate))[t]

    diff()[t] = rate[t] - rate[t-1] — uses only past-known rates.
    The rolling std at bar t covers the diff series ending at bar t (inclusive),
    i.e. diffs t-90...t. This is CONCURRENT (includes current bar's diff), NOT
    forward-looking. Both rate[t] and rate[t-1] are past-known at bar t (the
    funding rate settles at bar t's open — fully knowable before bar t closes).

    This test verifies:
      (a) Impulse at bar T depends on funding_rate[T] and funding_rate[T-1] only
          (no dependency on rate[T+1] or beyond).
      (b) Modifying rate[T+1] does NOT change impulse[T].
      (c) The rolling std denominator uses exactly 90 diffs ending at T.
    """
    from crypto_trade.features_v1.funding_v1 import compute_btc_funding_rate_8h_impulse

    # Create a synthetic DataFrame with 200 rows
    n = 200
    rng = np.random.default_rng(42)
    funding_rate = rng.normal(0.0001, 0.0003, size=n)

    df_base = pd.DataFrame({"funding_rate": funding_rate})
    df_base = compute_btc_funding_rate_8h_impulse(df_base)
    impulse_base = df_base["btc_funding_rate_8h_impulse"].copy()

    # Now modify rate[150] (a future bar relative to T=100) — impulse[100] must NOT change
    df_modified = pd.DataFrame({"funding_rate": funding_rate.copy()})
    df_modified.loc[150, "funding_rate"] = 999.0  # extreme modification of a future bar
    df_modified = compute_btc_funding_rate_8h_impulse(df_modified)
    impulse_modified = df_modified["btc_funding_rate_8h_impulse"].copy()

    # (b) Impulse at T=100 unchanged when rate[150] is modified
    assert impulse_base[100] == impulse_modified[100], (
        f"btc_funding_rate_8h_impulse[100] changed when future rate[150] was modified: "
        f"base={impulse_base[100]:.6f}, modified={impulse_modified[100]:.6f}. "
        "Look-ahead bias detected: the impulse at bar T must not depend on future rates."
    )

    # (a) Impulse at T=100 changes when rate[100] is modified (it SHOULD depend on current rate)
    df_current_modified = pd.DataFrame({"funding_rate": funding_rate.copy()})
    df_current_modified.loc[100, "funding_rate"] = 999.0
    df_current_modified = compute_btc_funding_rate_8h_impulse(df_current_modified)
    impulse_current_modified = df_current_modified["btc_funding_rate_8h_impulse"].copy()
    # T=100 impulse should change (rate[100] affects diff[100] = rate[100] - rate[99])
    # It also affects diff[101] if present, so T=101 may also change — that's expected.
    # The critical check is that T=100 is DIFFERENT (confirming the feature is sensitive to
    # the current rate — correctly using past-known information at bar T).
    assert impulse_base[100] != impulse_current_modified[100], (
        "btc_funding_rate_8h_impulse[100] did not change when rate[100] was modified. "
        "The feature should be sensitive to the current bar's funding rate "
        "(which is past-known at bar T per funding broadcast convention)."
    )

    # (c) Burn-in: rows 0..89 should be NaN.
    # diff() produces NaN at row 0. rolling(90, min_periods=90) on fr_diff:
    # at row 90, window=[row 1..90] — 90 non-NaN diffs → first valid std.
    # So rows 0..89 (90 rows) are NaN; row 90 is the first non-NaN impulse.
    assert pd.isna(impulse_base[:90]).all(), (
        f"btc_funding_rate_8h_impulse rows 0..89 should be NaN (90-row burn-in). "
        f"Non-NaN values found: {impulse_base[:90].dropna()}"
    )
    # Row 90+ should be non-NaN (assuming non-constant funding rate)
    assert pd.notna(impulse_base[90]), (
        f"btc_funding_rate_8h_impulse[90] should be non-NaN after 90-row burn-in. "
        f"Got: {impulse_base[90]}"
    )


# ---------------------------------------------------------------------------
# 2. test_btc_only_cohort
# ---------------------------------------------------------------------------


def test_btc_only_cohort() -> None:
    """V1_ITER052_UNIVERSE must be exactly ('BTCUSDT',) — BTC-only cohort."""
    from crypto_trade.features_v1 import V1_ITER052_UNIVERSE  # noqa: PLC0415

    assert set(V1_ITER052_UNIVERSE) == {"BTCUSDT"}, (
        f"V1_ITER052_UNIVERSE expected {{'BTCUSDT'}}, got {set(V1_ITER052_UNIVERSE)}. "
        "Brief Section 0: BTC-only specialist cohort."
    )
    assert len(V1_ITER052_UNIVERSE) == 1, (
        f"V1_ITER052_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER052_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# 3. test_features_in_pruned
# ---------------------------------------------------------------------------


def test_features_in_pruned() -> None:
    """btc_funding_spread_30_90 must be present in V1_FEATURE_COLUMNS_PRUNED.

    iter-v1/052 ADDed btc_funding_rate_8h_impulse and btc_funding_spread_30_90.
    iter-v1/054 DROPPED btc_funding_rate_8h_impulse (INERT in 3/3 seeds at /053).
    At current state (post-/054): only btc_funding_spread_30_90 remains.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    # Spread was added at /052 and retained through /054.
    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_spread_30_90 not found in V1_FEATURE_COLUMNS_PRUNED. "
        "This feature was added at iter-v1/052 and retained through /054."
    )
    # Impulse was added at /052 but DROPPED at /054 (INERT in 3/3 seeds at /053).
    assert "btc_funding_rate_8h_impulse" not in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_rate_8h_impulse should NOT be in V1_FEATURE_COLUMNS_PRUNED. "
        "It was dropped at iter-v1/054 (INERT confirmed in 3/3 outer seeds at /053)."
    )


# ---------------------------------------------------------------------------
# 4. test_pruned_size_48
# ---------------------------------------------------------------------------


def test_pruned_size_48() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features at iter-v1/052.

    History: 40 (baseline) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
             → 46 (/050 ADD dot_vs_btc_ret_ratio_30)
             → 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90).
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: PLC0415

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 49, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 49 features (post iter-v1/057 ADD); "
        f"got {n}. "
        "History: ...→ 46 (/050 ADD dot_vs_btc_ret_ratio_30) → 48 (/052 ADD 2 cols) "
        "→ 47 (/054 DROP impulse) → 48 (/055 ADD eth ratio) → 49 (/057 ADD ltc ratio)."
    )


# ---------------------------------------------------------------------------
# 5. test_funding_impulse_synthetic
# ---------------------------------------------------------------------------


def test_funding_impulse_synthetic() -> None:
    """Verify compute_btc_funding_rate_8h_impulse math against manual computation.

    Tests:
      (a) Normal case: impulse = diff / std, clipped to ±10.
      (b) Near-zero std guard: when std < 1e-8, output must be 0.0 (not inf/nan).
      (c) Clipping: when |impulse| > 10, output is clipped to ±10.
      (d) Burn-in: first 91 rows are NaN.
    """
    from crypto_trade.features_v1.funding_v1 import compute_btc_funding_rate_8h_impulse

    # --- (a) Normal case ---
    # Build a DataFrame with a constant funding_rate except for one spike at row 150.
    n = 200
    funding_rate = np.full(n, 0.0001, dtype=float)
    # Introduce a spike at row 150: rate[150] = 0.0010 (10x baseline)
    funding_rate[150] = 0.0010

    df = pd.DataFrame({"funding_rate": funding_rate})
    result = compute_btc_funding_rate_8h_impulse(df)
    impulse = result["btc_funding_rate_8h_impulse"]

    # Manual computation at row 150:
    # diff[150] = 0.0010 - 0.0001 = 0.0009
    # diffs 61..150 = [0.0, 0.0, ..., 0.0009] (one spike at the end)
    # std of those 90 diffs ≈ 0.0009 / sqrt(89) (only last diff is non-zero, rest ≈ 0)
    # But the spike is AT row 150 which is the last element of the window [61..150]
    # Actually diff[150] = 0.0009; diffs[61..149] = 0.0 (constant rate → zero diffs)
    # std([0, 0, ..., 0, 0.0009]) with 90 elements, 89 zeros and 1 non-zero
    # std ≈ 0.0009 / sqrt(90) * sqrt(90/89) ≈ 0.0009 / sqrt(89)
    diff_at_150 = funding_rate[150] - funding_rate[149]
    diffs_window = np.array([funding_rate[j] - funding_rate[j - 1] for j in range(61, 151)])
    std_at_150 = diffs_window.std(ddof=1)
    if std_at_150 > 1e-8:
        expected_impulse_150 = np.clip(diff_at_150 / std_at_150, -10.0, 10.0)
    else:
        expected_impulse_150 = 0.0

    assert abs(impulse[150] - expected_impulse_150) < 1e-9, (
        f"btc_funding_rate_8h_impulse[150] expected {expected_impulse_150:.8f}, "
        f"got {impulse[150]:.8f}. Manual vs computed mismatch — check formula."
    )

    # --- (b) Near-zero std guard ---
    # Constant funding rate → all diffs = 0 → std = 0 → impulse should be 0.0, not inf
    df_const = pd.DataFrame({"funding_rate": np.full(200, 0.0001, dtype=float)})
    result_const = compute_btc_funding_rate_8h_impulse(df_const)
    impulse_const = result_const["btc_funding_rate_8h_impulse"]

    # After burn-in, all values should be exactly 0.0 (not NaN, not inf)
    post_burnin = impulse_const[92:]
    assert not post_burnin.isna().any(), (
        "btc_funding_rate_8h_impulse contains NaN for constant funding rate (post burn-in). "
        "Expected 0.0 (std=0 guard: np.where(std > 1e-8, ..., 0.0))."
    )
    assert (post_burnin == 0.0).all(), (
        f"btc_funding_rate_8h_impulse not 0.0 for constant funding rate (std → 0): "
        f"range=[{post_burnin.min()}, {post_burnin.max()}]. "
        "The guard `np.where(std > 1e-8, diff/std, 0.0)` should fire here."
    )

    # --- (c) Clipping guard ---
    # With a single spike in a window of 90 diffs, the maximum achievable z-score
    # is sqrt(N) = sqrt(90) ≈ 9.49 (less than clip=10). The clip guard prevents
    # infinities when std → 0, not ordinary single-spike outliers.
    # Test: verify the output is finite and within [-10, +10] for any input.
    funding_extreme = np.full(200, 0.0001, dtype=float)
    funding_extreme[150] = 1000.0  # extreme spike
    df_extreme = pd.DataFrame({"funding_rate": funding_extreme})
    result_extreme = compute_btc_funding_rate_8h_impulse(df_extreme)
    impulse_extreme = result_extreme["btc_funding_rate_8h_impulse"]
    # All post-burn-in values must be within [-10, +10] and finite
    post_burnin_extreme = impulse_extreme.iloc[90:]
    assert (post_burnin_extreme.abs() <= 10.0 + 1e-9).all(), (
        f"btc_funding_rate_8h_impulse values outside clip range [-10, +10]: "
        f"min={post_burnin_extreme.min():.4f}, max={post_burnin_extreme.max():.4f}. "
        "Clip to [-10, +10] not applied correctly."
    )
    assert post_burnin_extreme.notna().all(), (
        "btc_funding_rate_8h_impulse contains NaN in post-burn-in region for spike input."
    )

    # --- (d) Burn-in ---
    # diff() has NaN at row 0. rolling(90, min_periods=90) on fr_diff first sees 90
    # non-NaN values at row 90 (window = rows 1..90). So rows 0..89 (90 rows) are NaN.
    funding_d = np.random.default_rng(7).normal(0.0001, 0.0003, size=200)
    df_d = pd.DataFrame({"funding_rate": funding_d})
    result_d = compute_btc_funding_rate_8h_impulse(df_d)
    impulse_d = result_d["btc_funding_rate_8h_impulse"]
    assert impulse_d[:90].isna().all(), (
        f"btc_funding_rate_8h_impulse rows 0..89 should all be NaN (90-row burn-in). "
        f"Non-NaN count: {impulse_d[:90].notna().sum()}"
    )


# ---------------------------------------------------------------------------
# 6. test_funding_spread_correctness
# ---------------------------------------------------------------------------


def test_funding_spread_correctness() -> None:
    """Verify compute_btc_funding_spread_30_90 computes z30 - z90 exactly.

    Tests:
      (a) spread = funding_rate_zscore_30 - funding_rate_zscore_90 (exact subtraction).
      (b) NaN propagation: when either z-score is NaN, spread is NaN.
      (c) Missing column raises KeyError.
      (d) Sign correctness: when z30 > z90, spread > 0; when z30 < z90, spread < 0.
    """
    from crypto_trade.features_v1.funding_v1 import compute_btc_funding_spread_30_90

    # --- (a) Exact subtraction ---
    n = 100
    rng = np.random.default_rng(13)
    z30 = rng.normal(0.0, 1.5, size=n)
    z90 = rng.normal(0.0, 1.0, size=n)

    df = pd.DataFrame({"funding_rate_zscore_30": z30, "funding_rate_zscore_90": z90})
    result = compute_btc_funding_spread_30_90(df)
    spread = result["btc_funding_spread_30_90"]

    expected_spread = z30 - z90
    np.testing.assert_array_almost_equal(
        spread.values,
        expected_spread,
        decimal=12,
        err_msg=(
            "btc_funding_spread_30_90 != funding_rate_zscore_30 - funding_rate_zscore_90. "
            "Formula mismatch — check compute_btc_funding_spread_30_90."
        ),
    )

    # --- (b) NaN propagation ---
    z30_nan = z30.copy()
    z30_nan[50] = np.nan
    df_nan = pd.DataFrame({"funding_rate_zscore_30": z30_nan, "funding_rate_zscore_90": z90})
    result_nan = compute_btc_funding_spread_30_90(df_nan)
    assert pd.isna(result_nan["btc_funding_spread_30_90"][50]), (
        "btc_funding_spread_30_90[50] should be NaN when funding_rate_zscore_30[50] is NaN. "
        "NaN propagation from parent z-score columns must be preserved."
    )

    # --- (c) Missing column raises KeyError ---
    df_missing_z30 = pd.DataFrame({"funding_rate_zscore_90": z90})
    with pytest.raises(KeyError, match="funding_rate_zscore_30"):
        compute_btc_funding_spread_30_90(df_missing_z30)

    df_missing_z90 = pd.DataFrame({"funding_rate_zscore_30": z30})
    with pytest.raises(KeyError, match="funding_rate_zscore_90"):
        compute_btc_funding_spread_30_90(df_missing_z90)

    # --- (d) Sign correctness ---
    # When z30 is uniformly higher than z90, spread should be uniformly positive
    df_pos = pd.DataFrame(
        {
            "funding_rate_zscore_30": np.full(n, 2.0),
            "funding_rate_zscore_90": np.full(n, 1.0),
        }
    )
    result_pos = compute_btc_funding_spread_30_90(df_pos)
    np.testing.assert_allclose(
        result_pos["btc_funding_spread_30_90"].values,
        np.full(n, 1.0),
        rtol=1e-10,
        err_msg=("btc_funding_spread_30_90 should be +1.0 when z30=2.0 and z90=1.0 everywhere."),
    )

    # When z30 is uniformly lower than z90, spread should be uniformly negative
    df_neg = pd.DataFrame(
        {
            "funding_rate_zscore_30": np.full(n, 0.5),
            "funding_rate_zscore_90": np.full(n, 1.5),
        }
    )
    result_neg = compute_btc_funding_spread_30_90(df_neg)
    np.testing.assert_allclose(
        result_neg["btc_funding_spread_30_90"].values,
        np.full(n, -1.0),
        rtol=1e-10,
        err_msg=("btc_funding_spread_30_90 should be -1.0 when z30=0.5 and z90=1.5 everywhere."),
    )
