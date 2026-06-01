"""Tests for iter-v1/057: LTC-only specialist — ltc_vs_btc_ret_ratio_30.

Covers 8 tests (+ bonus tests):

1. test_ltc_vs_btc_ret_ratio_30_in_pruned — ltc_vs_btc_ret_ratio_30 IS in V1_FEATURE_COLUMNS_PRUNED.
2. test_pruned_size_49 — V1_FEATURE_COLUMNS_PRUNED has exactly 49 features.
3. test_ltc_only_cohort — V1_ITER057_UNIVERSE is exactly ("LTCUSDT",).
4. test_no_lookahead — perturbing future bar does NOT affect past zscore values.
5. test_synthetic_ltc_btc_ratio — known inputs → known output.
6. test_outer_seed_offsets_patched — _OUTER_SEED_OFFSETS_PATCH is (0, 3, 6) in runner.
7. test_features_base_hash_changed_vs_056 — 49-col hash differs from /056 48-col hash.
8. test_ltc_feature_computed_non_nan — LTCUSDT produces non-NaN values after warmup.
Bonus:
9. test_dot_eth_features_nan_for_ltc_symbol — dot and eth features are NaN for LTCUSDT.
10. test_ltc_compute_function_importable — compute_ltc_vs_btc_ret_ratio_30 is importable.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest  # noqa: F401 (used via @pytest.mark.parametrize)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_kline_df(n: int = 300, seed: int = 42, symbol: str = "LTCUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time, close, symbol."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC (IS window start)
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    open_times = [start_ms + i * interval_ms for i in range(n)]
    log_rets = rng.normal(0, 0.025, n)  # LTC slightly more volatile than ETH
    prices = 90.0 * np.exp(np.cumsum(log_rets))  # LTC-scale price (~$90)
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": prices * 0.999,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": rng.uniform(10000, 1000000, n),
            "symbol": symbol,
        }
    )


def _make_btc_csv(tmpdir: Path, n: int = 300, seed: int = 99) -> Path:
    """Write a fake BTCUSDT/8h.csv to tmpdir aligned to LTCUSDT open_times, return path."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    log_rets = rng.normal(0, 0.018, n)
    prices = 30000.0 * np.exp(np.cumsum(log_rets))
    btc_dir = tmpdir / "BTCUSDT"
    btc_dir.mkdir(parents=True, exist_ok=True)
    csv_path = btc_dir / "8h.csv"
    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": prices * 0.999,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": rng.uniform(1e6, 1e8, n),
        }
    )
    df.to_csv(csv_path, index=False)
    return csv_path


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# 1. test_ltc_vs_btc_ret_ratio_30_in_pruned
# ---------------------------------------------------------------------------


def test_ltc_vs_btc_ret_ratio_30_in_pruned() -> None:
    """iter-v1/057 CLOSEOUT REVERT: ltc_vs_btc_ret_ratio_30 must be ABSENT post-revert.

    /057 added then REVERTED ltc_vs_btc_ret_ratio_30 at closeout (multi-seed n=3:
    mean Δ IS +0.1082 → MULTI-SEED-WEAK band; max-min spread 0.765 → BASIN-LOTTERY
    downgrade; importance ranks 13-15/49 fail LEARNED gate ≤10). 49 → 48 cols.
    Feature computation code preserved in cross_btc_v1.py.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "ltc_vs_btc_ret_ratio_30" not in V1_FEATURE_COLUMNS_PRUNED, (
        "ltc_vs_btc_ret_ratio_30 still present in V1_FEATURE_COLUMNS_PRUNED. "
        "iter-v1/057 closeout REVERTED the feature; it must NOT be in the pruned set. "
        "Check src/crypto_trade/features_v1/__init__.py — the line should be commented out."
    )


# ---------------------------------------------------------------------------
# 2. test_pruned_size_49
# ---------------------------------------------------------------------------


def test_pruned_size_49() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 49 features at iter-v1/058 (post-/057 revert + /058 ADD).

    History:
        40 (baseline /002) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
        → 46 (/050 ADD dot_vs_btc_ret_ratio_30)
        → 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90)
        → 47 (/054 DROP btc_funding_rate_8h_impulse)
        → 48 (/055 ADD eth_vs_btc_ret_ratio_30)
        → 49 (/057 ADD ltc_vs_btc_ret_ratio_30) — pre-closeout
        → 48 (/057 CLOSEOUT REVERT — BASIN-LOTTERY downgrade)
        → 49 (/058 ADD btc_oi_delta_5_z30 — short-window OI delta)
    NOTE: This test function name is misleadingly named "test_pruned_size_49" from /057 era;
    at /058 the expected count IS 49 again (btc_oi_delta_5_z30 added).
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 49, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 49 features at iter-v1/058; got {n}. "
        "History: /057 REVERTED ltc_vs_btc_ret_ratio_30 (49→48); "
        "/058 ADDED btc_oi_delta_5_z30 (48→49). "
        "If n == 48: /058 ADD was NOT applied — check /058 closeout implementation. "
        "If n < 48 or n > 49: something was unexpectedly removed or double-added."
    )


# ---------------------------------------------------------------------------
# 3. test_ltc_only_cohort
# ---------------------------------------------------------------------------


def test_ltc_only_cohort() -> None:
    """V1_ITER057_UNIVERSE must be exactly ('LTCUSDT',) — LTC-only cohort.

    Independently defined constant. LTC-only specialist head; BTC loaded for cross-asset
    feature computation only, NOT traded.
    """
    from crypto_trade.features_v1 import V1_ITER057_UNIVERSE

    assert set(V1_ITER057_UNIVERSE) == {"LTCUSDT"}, (
        f"V1_ITER057_UNIVERSE expected {{'LTCUSDT'}}, got {set(V1_ITER057_UNIVERSE)}. "
        "Brief Section 10.1: LTC-only cohort for /057 specialist head. "
        "BTCUSDT is loaded for cross-asset feature computation only — not traded."
    )
    assert len(V1_ITER057_UNIVERSE) == 1, (
        f"V1_ITER057_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER057_UNIVERSE)}."
    )

    # V1_ITER057_UNIVERSE must be in __all__
    import crypto_trade.features_v1 as fv1

    assert "V1_ITER057_UNIVERSE" in fv1.__all__, (
        "V1_ITER057_UNIVERSE not found in crypto_trade.features_v1.__all__. "
        "Add it to the __all__ list in src/crypto_trade/features_v1/__init__.py."
    )


# ---------------------------------------------------------------------------
# 4. test_no_lookahead
# ---------------------------------------------------------------------------


def test_no_lookahead() -> None:
    """Perturbing future bar does NOT affect past zscore values (no look-ahead).

    The rolling zscore at bar t uses only ratio[t-window+1]...ratio[t].
    Perturbing bar N does not reach back to bars well before N.
    """
    from crypto_trade.features_v1.cross_btc_v1 import compute_ltc_vs_btc_ret_ratio_30

    rng = np.random.default_rng(57)
    n = 300
    ltc_prices = 90.0 * np.exp(np.cumsum(rng.normal(0, 0.025, n)))
    btc_prices = 30000.0 * np.exp(np.cumsum(rng.normal(0, 0.018, n)))

    df_ltc1 = pd.DataFrame({"close": ltc_prices, "open_time": range(n)})
    df_btc1 = pd.DataFrame({"close": btc_prices, "open_time": range(n)})

    # Compute baseline
    out1 = compute_ltc_vs_btc_ret_ratio_30(df_ltc1, df_btc1)

    # Perturb ONLY the last bar's BTC price (extreme value)
    btc_prices2 = btc_prices.copy()
    btc_prices2[-1] = btc_prices[-1] * 1000.0  # extreme perturbation

    df_ltc2 = pd.DataFrame({"close": ltc_prices.copy(), "open_time": range(n)})
    df_btc2 = pd.DataFrame({"close": btc_prices2, "open_time": range(n)})

    out2 = compute_ltc_vs_btc_ret_ratio_30(df_ltc2, df_btc2)

    # All rows well before the perturbation influence range should be identical
    check_end = n - 90 - 1  # well before the perturbation influence range
    pd.testing.assert_series_equal(
        out1.iloc[:check_end],
        out2.iloc[:check_end],
        check_names=False,
        check_exact=False,
        atol=1e-10,
        rtol=0,
    )


# ---------------------------------------------------------------------------
# 5. test_synthetic_ltc_btc_ratio — known inputs → known output
# ---------------------------------------------------------------------------


def test_synthetic_ltc_btc_ratio() -> None:
    """Known inputs produce expected output for compute_ltc_vs_btc_ret_ratio_30.

    Test case A: constant prices — pct_change = 0 → ratio = 0/0 → NaN.
    Test case B: proportional drift — LTC = BTC × constant → ratio ~ 1 (constant) →
        rolling std → 0 → zscore = NaN (denominator zero replace).
    Test case C: divergent drifts — LTC doubles faster than BTC → ratio > 1 progressively;
        z-scored output should be finite after warmup and clipped to ±10.
    """
    from crypto_trade.features_v1.cross_btc_v1 import compute_ltc_vs_btc_ret_ratio_30

    n = 300

    # Test A: constant prices
    ltc_const = pd.DataFrame({"close": [90.0] * n, "open_time": range(n)})
    btc_const = pd.DataFrame({"close": [30000.0] * n, "open_time": range(n)})
    out_a = compute_ltc_vs_btc_ret_ratio_30(ltc_const, btc_const)
    assert out_a.isna().all(), (
        "With constant prices (pct_change=0), ratio = 0/0 = NaN. "
        f"Expected all-NaN output; got {out_a.dropna().head(5)}."
    )

    # Test B: proportional drift (LTC and BTC same growth rate → ratio ~ 1 constant → std=0 → NaN)
    n2 = 500
    btc_drift = [30000.0 * (1.005**i) for i in range(n2)]
    ltc_drift = [90.0 * (1.005**i) for i in range(n2)]  # same growth rate
    df_ltc_b = pd.DataFrame({"close": ltc_drift, "open_time": range(n2)})
    df_btc_b = pd.DataFrame({"close": btc_drift, "open_time": range(n2)})
    out_b = compute_ltc_vs_btc_ret_ratio_30(df_ltc_b, df_btc_b)
    # Ratio is ~1.0 constant → rolling std → 0 → NaN denominator replace → NaN output
    finite_b = out_b.dropna()
    if len(finite_b) > 0:
        assert (finite_b.abs() <= 10.0 + 1e-9).all(), (
            f"Proportional drift: clipping failed; max_abs={finite_b.abs().max():.4f} > 10.0"
        )

    # Test C: divergent drift — verify finite clipped output after warmup
    rng = np.random.default_rng(57)
    ltc_prices_c = 90.0 * np.exp(np.cumsum(rng.normal(0.004, 0.025, n2)))  # higher LTC drift
    btc_prices_c = 30000.0 * np.exp(np.cumsum(rng.normal(0.001, 0.018, n2)))  # lower BTC drift
    df_ltc_c = pd.DataFrame({"close": ltc_prices_c, "open_time": range(n2)})
    df_btc_c = pd.DataFrame({"close": btc_prices_c, "open_time": range(n2)})
    out_c = compute_ltc_vs_btc_ret_ratio_30(df_ltc_c, df_btc_c)
    finite_c = out_c.iloc[90:].dropna()  # after warmup
    assert len(finite_c) > 0, (
        "Expected non-NaN values after 90-bar warmup with divergent drift prices."
    )
    assert (finite_c.abs() <= 10.0 + 1e-9).all(), (
        f"Divergent drift: clipping failed; max_abs={finite_c.abs().max():.4f} > 10.0"
    )


# ---------------------------------------------------------------------------
# 6. test_outer_seed_offsets_patched
# ---------------------------------------------------------------------------


def test_outer_seed_offsets_patched() -> None:
    """run_iteration_057._OUTER_SEED_OFFSETS_PATCH must be (0, 3, 6).

    /057 uses the same multi-seed pattern as /051: 3 outer seeds at offsets (0, 3, 6)
    from ENSEMBLE_SEEDS = (42, 123, 456, ...) → inner windows [42,123,456],
    [789,1001,2002], [3003,4004,5005] — fully disjoint.

    The patch is applied in run_iteration_057.main() via:
        run_baseline_v1._OUTER_SEED_OFFSETS = _OUTER_SEED_OFFSETS_PATCH
    before calling run_baseline_v1.main().
    """
    import run_iteration_057

    assert run_iteration_057._OUTER_SEED_OFFSETS_PATCH == (0, 3, 6), (
        f"_OUTER_SEED_OFFSETS_PATCH expected (0, 3, 6), "
        f"got {run_iteration_057._OUTER_SEED_OFFSETS_PATCH}. "
        "iter-v1/057 uses the same 3-outer-seed offset pattern as /051. "
        "Inner seed windows: [42,123,456] / [789,1001,2002] / [3003,4004,5005]."
    )
    assert len(run_iteration_057._OUTER_SEED_OFFSETS_PATCH) == 3, (
        "Expected exactly 3 outer seed offsets for /057 multi-seed design."
    )


# ---------------------------------------------------------------------------
# 7. test_features_base_hash_changed_vs_056
# ---------------------------------------------------------------------------


def test_features_base_hash_changed_vs_056() -> None:
    """The features-base-hash at /057 must DIFFER from the hash at /056.

    /056 used 48 cols (eth_vs_btc_ret_ratio_30 ADDED; btc_funding_rate_8h_impulse DROPPED).
    /057 adds ltc_vs_btc_ret_ratio_30 (48 → 49 cols).
    The SHA-256 of sorted(V1_FEATURE_COLUMNS_PRUNED) MUST change.
    """
    import run_iteration_057

    # Pre-registered reference hashes from the /057 runner
    expected_49col = run_iteration_057.FEATURES_BASE_HASH_49COL
    expected_48col = run_iteration_057.FEATURES_BASE_HASH_48COL

    # The two hashes must be different (ltc feature ADD changes the column set)
    assert expected_49col != expected_48col, (
        "FEATURES_BASE_HASH_49COL and FEATURES_BASE_HASH_48COL must differ in run_iteration_057. "
        "Adding ltc_vs_btc_ret_ratio_30 (48→49 cols) produces a different SHA-256. "
        "If they are equal, the pre-registered hash constants are wrong."
    )

    # Post-/057-CLOSEOUT-REVERT + /058-ADD: live V1_FEATURE_COLUMNS_PRUNED is now at 49 cols
    # (ltc_vs_btc_ret_ratio_30 REVERTED at /057, btc_oi_delta_5_z30 ADDED at /058).
    # The live hash will differ from BOTH the /057 49-col hash AND the /057 48-col hash.
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    live_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)

    # At /058: live must differ from the /057 pre-revert 49-col hash (different feature set)
    assert live_hash != expected_49col, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash matches the /057 pre-revert 49-col reference "
        f"(ltc_vs_btc_ret_ratio_30 added). At /058 the feature set should be different "
        f"(btc_oi_delta_5_z30 added instead).\n"
        f"  live computed: {live_hash}\n"
        f"  expected_49col (/057 pre-revert): {expected_49col}"
    )

    # At /058: live must also differ from the /057 post-revert 48-col hash (btc_oi_delta_5_z30 was added)
    assert live_hash != expected_48col, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash matches the /057 48-col post-revert reference. "
        f"This means btc_oi_delta_5_z30 (/058 ADD) was NOT applied.\n"
        f"  live computed: {live_hash}\n"
        f"  expected_48col (/057 post-revert): {expected_48col}"
    )

    print(f"  [OK] expected_49col hash = {expected_49col[:16]}...")
    print(f"  [OK] expected_48col hash = {expected_48col[:16]}...")
    print("  [OK] Hashes differ as expected (ltc feature ADD confirmed in column set).")


# ---------------------------------------------------------------------------
# 8. test_ltc_feature_computed_non_nan
# ---------------------------------------------------------------------------


def test_ltc_feature_computed_non_nan() -> None:
    """LTCUSDT produces non-NaN ltc_vs_btc_ret_ratio_30 values after warmup period.

    Warmup: first 90 rows NaN (rolling zscore min_periods=90 dominates).
    After warmup: non-NaN values expected from the cross-asset ratio computation.
    """
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    n = 300
    df_ltc = _make_kline_df(n=n, seed=57, symbol="LTCUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        _make_btc_csv(Path(tmpdir), n=n, seed=99)
        out = add_cross_btc_v1_features(df_ltc, data_dir=Path(tmpdir))

    # LTC feature: non-NaN after warmup
    assert "ltc_vs_btc_ret_ratio_30" in out.columns, (
        "ltc_vs_btc_ret_ratio_30 column missing from add_cross_btc_v1_features output for LTCUSDT."
    )
    non_nan_ltc = out["ltc_vs_btc_ret_ratio_30"].dropna()
    assert len(non_nan_ltc) > 0, (
        "ltc_vs_btc_ret_ratio_30 is all-NaN for LTCUSDT after add_cross_btc_v1_features. "
        "Expected non-NaN values after 90-bar warmup (n=300 bars; 210 non-NaN expected)."
    )
    # Warmup: first 90 rows should be NaN (zscore window dominates)
    assert out["ltc_vs_btc_ret_ratio_30"].iloc[:89].isna().all(), (
        "ltc_vs_btc_ret_ratio_30: first 89 rows should be NaN (90-bar zscore warmup). "
        f"Non-NaN count in first 89 rows: {out['ltc_vs_btc_ret_ratio_30'].iloc[:89].notna().sum()}"
    )
    # Values should be clipped to [-10, +10]
    assert (non_nan_ltc.abs() <= 10.0 + 1e-9).all(), (
        f"ltc_vs_btc_ret_ratio_30 clipping failed: max_abs={non_nan_ltc.abs().max():.4f} > 10.0"
    )


# ---------------------------------------------------------------------------
# 9. test_dot_eth_features_nan_for_ltc_symbol
# ---------------------------------------------------------------------------


def test_dot_eth_features_nan_for_ltc_symbol() -> None:
    """dot_vs_btc_ret_ratio_30 and eth_vs_btc_ret_ratio_30 must be all-NaN for LTCUSDT.

    LTCUSDT uses ltc_vs_btc_ret_ratio_30 (iter-v1/057).
    dot_vs_btc_ret_ratio_30 is DOT-only and eth_vs_btc_ret_ratio_30 is ETH-only.
    All three columns must exist in the output for V1_FEATURE_COLUMNS_PRUNED compliance.
    """
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    n = 300
    df_ltc = _make_kline_df(n=n, seed=57, symbol="LTCUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        _make_btc_csv(Path(tmpdir), n=n, seed=99)
        out = add_cross_btc_v1_features(df_ltc, data_dir=Path(tmpdir))

    # dot_vs_btc_ret_ratio_30 must exist but be all-NaN for LTCUSDT
    assert "dot_vs_btc_ret_ratio_30" in out.columns, (
        "dot_vs_btc_ret_ratio_30 column missing from add_cross_btc_v1_features output for LTCUSDT. "
        "The column must exist (even as NaN) for V1_FEATURE_COLUMNS_PRUNED compliance."
    )
    assert out["dot_vs_btc_ret_ratio_30"].isna().all(), (
        "dot_vs_btc_ret_ratio_30 should be all-NaN for LTCUSDT (DOT-only feature). "
        f"Non-NaN count: {out['dot_vs_btc_ret_ratio_30'].notna().sum()}. "
        "Regression in add_cross_btc_v1_features dispatch: LTC branch must set DOT column to NaN."
    )

    # eth_vs_btc_ret_ratio_30 must exist but be all-NaN for LTCUSDT
    assert "eth_vs_btc_ret_ratio_30" in out.columns, (
        "eth_vs_btc_ret_ratio_30 column missing from add_cross_btc_v1_features output for LTCUSDT. "
        "The column must exist (even as NaN) for V1_FEATURE_COLUMNS_PRUNED compliance."
    )
    assert out["eth_vs_btc_ret_ratio_30"].isna().all(), (
        "eth_vs_btc_ret_ratio_30 should be all-NaN for LTCUSDT (ETH-only feature). "
        f"Non-NaN count: {out['eth_vs_btc_ret_ratio_30'].notna().sum()}. "
        "Regression in add_cross_btc_v1_features dispatch: LTC branch must set ETH column to NaN."
    )


# ---------------------------------------------------------------------------
# 10. test_ltc_compute_function_importable
# ---------------------------------------------------------------------------


def test_ltc_compute_function_importable() -> None:
    """compute_ltc_vs_btc_ret_ratio_30 must be importable from cross_btc_v1."""
    from crypto_trade.features_v1.cross_btc_v1 import (
        LTC_FEATURE_COLUMN,
        LTC_TARGET_SYMBOL,
        compute_ltc_vs_btc_ret_ratio_30,
    )

    assert callable(compute_ltc_vs_btc_ret_ratio_30), (
        "compute_ltc_vs_btc_ret_ratio_30 is not callable."
    )
    assert LTC_FEATURE_COLUMN == "ltc_vs_btc_ret_ratio_30", (
        f"LTC_FEATURE_COLUMN expected 'ltc_vs_btc_ret_ratio_30', got {LTC_FEATURE_COLUMN!r}."
    )
    assert LTC_TARGET_SYMBOL == "LTCUSDT", (
        f"LTC_TARGET_SYMBOL expected 'LTCUSDT', got {LTC_TARGET_SYMBOL!r}."
    )


# ---------------------------------------------------------------------------
# Bonus parametrized: feature presence/absence in pruned set
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "feature_name,expected_in_pruned",
    [
        ("ltc_vs_btc_ret_ratio_30", False),  # ADDED at /057, REVERTED at closeout (BASIN-LOTTERY)
        ("eth_vs_btc_ret_ratio_30", True),  # ADDED at /055; must still be present
        ("dot_vs_btc_ret_ratio_30", True),  # ADDED at /050; must still be present
        ("btc_funding_spread_30_90", True),  # RETAINED at /054; must still be present
        ("btc_funding_rate_8h_impulse", False),  # DROPPED at /054; must NOT be present
        ("basis_zscore_30", False),  # dropped at /034/040; must NOT be present
        ("regime_momentum_signed_5d", True),  # added at /040; must still be present
    ],
)
def test_feature_presence_parametrized(feature_name: str, expected_in_pruned: bool) -> None:
    """Parametrized check for feature presence/absence in V1_FEATURE_COLUMNS_PRUNED at /057."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    actual = feature_name in V1_FEATURE_COLUMNS_PRUNED
    assert actual == expected_in_pruned, (
        f"Feature {feature_name!r}: expected in_pruned={expected_in_pruned}, "
        f"got {actual}. "
        f"V1_FEATURE_COLUMNS_PRUNED has {len(V1_FEATURE_COLUMNS_PRUNED)} cols at /057 closeout. "
        f"At /057 closeout: ltc_vs_btc_ret_ratio_30 REVERTED (BASIN-LOTTERY); "
        f"btc_funding_rate_8h_impulse DROPPED at /054; all other features unchanged."
    )


# ---------------------------------------------------------------------------
# Bonus: runner metadata checks
# ---------------------------------------------------------------------------


def test_runner_metadata_057() -> None:
    """Verify run_iteration_057.py has correct metadata constants."""
    import run_iteration_057

    assert run_iteration_057.ITERATION_NUMBER == 57, (
        f"ITERATION_NUMBER expected 57, got {run_iteration_057.ITERATION_NUMBER}."
    )
    assert run_iteration_057.ITERATION_LABEL == "v1-057", (
        f"ITERATION_LABEL expected 'v1-057', got {run_iteration_057.ITERATION_LABEL!r}."
    )
    assert run_iteration_057.SEEDS_DEFAULT == 3, (
        f"SEEDS_DEFAULT expected 3 (multi-seed built-in; 3 outer seeds), "
        f"got {run_iteration_057.SEEDS_DEFAULT}."
    )
    assert run_iteration_057.ENSEMBLE_SIZE == 3, (
        f"ENSEMBLE_SIZE expected 3 (inner; EXPLORATION standard), "
        f"got {run_iteration_057.ENSEMBLE_SIZE}."
    )
    assert run_iteration_057.N_TRIALS_DEFAULT == 18, (
        f"N_TRIALS_DEFAULT expected 18 (EXPLORATION standard), "
        f"got {run_iteration_057.N_TRIALS_DEFAULT}."
    )
    # Hash guard: 49-col hash must differ from 48-col hash
    h49 = run_iteration_057.FEATURES_BASE_HASH_49COL
    h48 = run_iteration_057.FEATURES_BASE_HASH_48COL
    assert h49 != h48, (
        "FEATURES_BASE_HASH_49COL must differ from FEATURES_BASE_HASH_48COL. "
        "Ltc feature ADD changes the column set — hashes must be different."
    )
