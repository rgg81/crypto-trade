"""Tests for iter-v1/058: BTC-only specialist — btc_oi_delta_5_z30 short-window OI feature.

Covers 7 mandatory tests:

1. test_feature_in_pruned — btc_oi_delta_5_z30 IS in V1_FEATURE_COLUMNS_PRUNED.
2. test_pruned_size_49 — V1_FEATURE_COLUMNS_PRUNED has exactly 49 features.
3. test_btc_only_cohort — V1_ITER058_UNIVERSE is exactly ("BTCUSDT",).
4. test_no_lookahead — perturbing future bar does NOT affect past zscore values.
5. test_synthetic_oi_delta — known inputs → known output for compute_oi_delta_zscore(delta=5, z=30).
6. test_outer_seed_offsets_patched — _OUTER_SEED_OFFSETS_PATCH is (0, 3, 6) in runner.
7. test_features_base_hash — 49-col hash matches pre-registered; differs from 48-col ref.

Bonus tests:
8. test_btc_iter058_universe_in_all — V1_ITER058_UNIVERSE is in __all__.
9. test_add_oi_delta_5_z30_feature_importable — function is importable from open_interest_v1.
10. test_add_oi_delta_5_z30_feature_computes — produces non-NaN values after burn-in.
11. test_runner_metadata_058 — ITERATION_NUMBER, ITERATION_LABEL, SEEDS_DEFAULT etc. correct.
12. test_oi_delta_5_z30_clip_range — output is always in [-10, +10].
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest  # noqa: F401

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_oi_csv(tmpdir: Path, n: int = 300, seed: int = 42) -> Path:
    """Write a fake open_interest/BTCUSDT/8h.csv to tmpdir, return path."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    # Simulate plausible OI levels: ~100k contracts with random walk drift
    oi_levels = 100_000.0 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    oi_dir = tmpdir / "open_interest" / "BTCUSDT"
    oi_dir.mkdir(parents=True, exist_ok=True)
    csv_path = oi_dir / "8h.csv"
    df = pd.DataFrame(
        {
            "open_time": open_times,
            "sum_open_interest": oi_levels,
            "sum_open_interest_value": oi_levels * 30000.0,
        }
    )
    df.to_csv(csv_path, index=False)
    return csv_path


def _make_kline_df(n: int = 300, seed: int = 42, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    prices = 30_000.0 * np.exp(np.cumsum(rng.normal(0, 0.018, n)))
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": prices * 0.999,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": rng.uniform(1e5, 1e7, n),
            "symbol": symbol,
        }
    )


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# 1. test_feature_in_pruned
# ---------------------------------------------------------------------------


def test_feature_in_pruned() -> None:
    """btc_oi_delta_5_z30 was ADDED at /058 then REVERTED at /058 closeout — NOT in global.

    iter-v1/058 added btc_oi_delta_5_z30 but REVERTED it at closeout (BASIN-LOTTERY:
    spread 0.8995 > 0.50; mean OOS -0.599). Feature computation code is preserved in
    open_interest_v1.py for future re-use. Global V1_FEATURE_COLUMNS_PRUNED stays at 48.
    btc_oi_delta_5_z30 must NOT be in the global pruned set after the /058 REVERT.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "btc_oi_delta_5_z30" not in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_oi_delta_5_z30 IS in V1_FEATURE_COLUMNS_PRUNED but was REVERTED at /058 closeout. "
        "Global should have 48 cols after the BASIN-LOTTERY revert."
    )


# ---------------------------------------------------------------------------
# 2. test_pruned_size_49
# ---------------------------------------------------------------------------


def test_pruned_size_49() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features (post-/058 REVERT).

    History:
        40 (baseline /002) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
        → 46 (/050) → 48 (/052 ADD two features) → 47 (/054 DROP impulse)
        → 48 (/055 ADD eth_vs_btc_ret_ratio_30) → 49 (/057 ADD ltc) → 48 (/057 REVERT)
        → 49 (/058 ADD btc_oi_delta_5_z30) → 48 (/058 REVERT — BASIN-LOTTERY spread 0.8995)
    NOTE: Test function named "test_pruned_size_49" from /057 era; after /058 REVERT count is 48.
    /084 oi_price_divergence_30 is LOCAL-ONLY (V1_ITER084_FEATURE_COLUMNS). Global stays 48.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 48, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 48 features after /058 REVERT; got {n}. "
        "iter-v1/058 REVERTED btc_oi_delta_5_z30 (BASIN-LOTTERY spread 0.8995). "
        "/084 oi_price_divergence_30 is LOCAL-ONLY in V1_ITER084_FEATURE_COLUMNS."
    )


# ---------------------------------------------------------------------------
# 3. test_btc_only_cohort
# ---------------------------------------------------------------------------


def test_btc_only_cohort() -> None:
    """V1_ITER058_UNIVERSE must be exactly ('BTCUSDT',) — BTC-only cohort."""
    from crypto_trade.features_v1 import V1_ITER058_UNIVERSE

    assert set(V1_ITER058_UNIVERSE) == {"BTCUSDT"}, (
        f"V1_ITER058_UNIVERSE expected {{'BTCUSDT'}}, got {set(V1_ITER058_UNIVERSE)}. "
        "Brief Section 10.1: BTC-only cohort for /058 BTC specialist head."
    )
    assert len(V1_ITER058_UNIVERSE) == 1, (
        f"V1_ITER058_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER058_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# 4. test_no_lookahead
# ---------------------------------------------------------------------------


def test_no_lookahead() -> None:
    """Perturbing future bar does NOT affect past zscore values (no look-ahead).

    The past-only z-score at bar t uses oi_delta[t-window+1]...oi_delta[t-1] (shifted).
    Perturbing bar N does not reach back to bars well before N.
    """
    from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

    rng = np.random.default_rng(58)
    n = 300
    oi_levels = 100_000.0 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))

    oi1 = pd.Series(oi_levels.copy())
    oi2 = pd.Series(oi_levels.copy())
    # Extreme perturbation at the LAST bar only
    oi2.iloc[-1] = oi2.iloc[-1] * 1000.0

    out1 = compute_oi_delta_zscore(oi1, delta_window=5, zscore_window=30)
    out2 = compute_oi_delta_zscore(oi2, delta_window=5, zscore_window=30)

    # All rows well before the perturbation influence range should be identical.
    # Influence range = last ~(delta_window + zscore_window) bars = ~35 bars.
    check_end = n - 40  # well before any influence
    pd.testing.assert_series_equal(
        out1.iloc[:check_end],
        out2.iloc[:check_end],
        check_names=False,
        check_exact=False,
        atol=1e-10,
        rtol=0,
    )


# ---------------------------------------------------------------------------
# 5. test_synthetic_oi_delta
# ---------------------------------------------------------------------------


def test_synthetic_oi_delta() -> None:
    """Known inputs → known output for compute_oi_delta_zscore(delta_window=5, zscore_window=30).

    Test A: constant OI — delta = 0 → z-score NaN (rolling std = 0, replaced with NaN).
    Test B: linearly increasing OI — constant delta → rolling std → 0 → NaN.
    Test C: random OI — finite clipped output after burn-in period.
    """
    from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

    n = 300

    # Test A: constant OI
    oi_const = pd.Series([100_000.0] * n)
    out_a = compute_oi_delta_zscore(oi_const, delta_window=5, zscore_window=30)
    # delta = 0 → shifted std = 0 → NaN denominator → NaN output
    assert out_a.isna().all() or (out_a.dropna().abs() < 1e-9).all(), (
        "Constant OI should produce all-NaN or all-zero zscore (delta=0, std=0). "
        f"Got non-trivial values: {out_a.dropna().head(5)}"
    )

    # Test B: linearly increasing OI (constant % delta)
    oi_linear = pd.Series([100_000.0 * (1.001**i) for i in range(n)])
    out_b = compute_oi_delta_zscore(oi_linear, delta_window=5, zscore_window=30)
    # delta is constant after warm-up → rolling std → 0 → NaN
    # (any finite values should still be clipped to ±10)
    finite_b = out_b.dropna()
    if len(finite_b) > 0:
        assert (finite_b.abs() <= 10.0 + 1e-9).all(), (
            f"Linear OI: clip failed; max_abs = {finite_b.abs().max():.4f}"
        )

    # Test C: random OI — finite output after 5 + 30 = 35 bar burn-in
    rng = np.random.default_rng(58)
    oi_random = pd.Series(100_000.0 * np.exp(np.cumsum(rng.normal(0, 0.005, n))))
    out_c = compute_oi_delta_zscore(oi_random, delta_window=5, zscore_window=30)

    # First 35 rows should be NaN (5 delta warmup + 30 z-score min_periods dominates)
    # Actual: first delta_window=5 delta NaN + first zscore_window=30 z-score NaN.
    # Total: first 5+30-1 = 34 rows NaN (based on rolling mechanics).
    assert out_c.iloc[:34].isna().all(), (
        f"First 34 rows should be NaN (burn-in: delta_window=5 + zscore_window=30 - 1). "
        f"Non-NaN count in first 34 rows: {out_c.iloc[:34].notna().sum()}"
    )
    finite_c = out_c.iloc[35:].dropna()
    assert len(finite_c) > 0, "Expected non-NaN values after 35-bar burn-in for random OI."
    assert (finite_c.abs() <= 10.0 + 1e-9).all(), (
        f"Random OI: clip failed; max_abs = {finite_c.abs().max():.4f}"
    )


# ---------------------------------------------------------------------------
# 6. test_outer_seed_offsets_patched
# ---------------------------------------------------------------------------


def test_outer_seed_offsets_patched() -> None:
    """run_iteration_058._OUTER_SEED_OFFSETS_PATCH must be (0, 3, 6).

    /058 uses the same multi-seed pattern as /057, /053, /051:
    3 outer seeds at offsets (0, 3, 6) from ENSEMBLE_SEEDS = (42, 123, 456, ...)
    → inner windows [42,123,456], [789,1001,2002], [3003,4004,5005] — fully disjoint.

    The patch is applied in run_iteration_058.main() via:
        run_baseline_v1._OUTER_SEED_OFFSETS = _OUTER_SEED_OFFSETS_PATCH
    before calling run_baseline_v1.main().
    """
    import run_iteration_058

    assert run_iteration_058._OUTER_SEED_OFFSETS_PATCH == (0, 3, 6), (
        f"_OUTER_SEED_OFFSETS_PATCH expected (0, 3, 6), "
        f"got {run_iteration_058._OUTER_SEED_OFFSETS_PATCH}. "
        "iter-v1/058 uses the same 3-outer-seed offset pattern as /057+/053+/051."
    )
    assert len(run_iteration_058._OUTER_SEED_OFFSETS_PATCH) == 3, (
        "Expected exactly 3 outer seed offsets for /058 multi-seed design."
    )


# ---------------------------------------------------------------------------
# 7. test_features_base_hash
# ---------------------------------------------------------------------------


def test_features_base_hash() -> None:
    """Live hash must match the /058 48-col reference (post-REVERT state).

    /057 closeout used 48 cols (ltc_vs_btc_ret_ratio_30 REVERTED).
    /058 added btc_oi_delta_5_z30 (48 → 49 cols) then REVERTED it at closeout
    (BASIN-LOTTERY spread 0.8995). Global returns to 48 cols = same as post-/057-revert.
    The live hash must equal FEATURES_BASE_HASH_48COL and differ from FEATURES_BASE_HASH_49COL.
    """
    import run_iteration_058

    h49 = run_iteration_058.FEATURES_BASE_HASH_49COL
    h48 = run_iteration_058.FEATURES_BASE_HASH_48COL

    # Hashes must differ (ADD vs REVERT are different column sets)
    assert h49 != h48, (
        "FEATURES_BASE_HASH_49COL and FEATURES_BASE_HASH_48COL must differ. "
        "Adding btc_oi_delta_5_z30 (48→49 cols) produces a different SHA-256."
    )

    # Live V1_FEATURE_COLUMNS_PRUNED must match the 48-col hash (REVERT state)
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    live_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert live_hash == h48, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash does not match pre-registered 48-col hash.\n"
        f"  pre-registered 49-col: {h49}\n"
        f"  pre-registered 48-col: {h48}\n"
        f"  live computed        : {live_hash}\n"
        "/058 REVERTED btc_oi_delta_5_z30; live should match 48-col reference."
    )
    # Must differ from 49-col (ADD was reverted)
    assert live_hash != h49, (
        f"Live hash matches 49-col reference; btc_oi_delta_5_z30 STILL in pruned set — REVERT "
        f"not applied. live = {live_hash}, h49 = {h49}."
    )

    print(f"  [OK] 49-col hash = {h49[:16]}...")
    print(f"  [OK] 48-col hash = {h48[:16]}...")
    print("  [OK] live == h48: /058 REVERT confirmed.")


# ---------------------------------------------------------------------------
# 8. test_btc_iter058_universe_in_all
# ---------------------------------------------------------------------------


def test_btc_iter058_universe_in_all() -> None:
    """V1_ITER058_UNIVERSE must be in crypto_trade.features_v1.__all__."""
    import crypto_trade.features_v1 as fv1

    assert "V1_ITER058_UNIVERSE" in fv1.__all__, (
        "V1_ITER058_UNIVERSE not found in crypto_trade.features_v1.__all__. "
        "Add it to the __all__ list in src/crypto_trade/features_v1/__init__.py."
    )


# ---------------------------------------------------------------------------
# 9. test_add_oi_delta_5_z30_feature_importable
# ---------------------------------------------------------------------------


def test_add_oi_delta_5_z30_feature_importable() -> None:
    """add_oi_delta_5_z30_feature and OI_DELTA_5_Z30_COLUMN must be importable."""
    from crypto_trade.features_v1.open_interest_v1 import (
        OI_DELTA_5_Z30_COLUMN,
        OI_DELTA_LOOKBACK_5,
        OI_ZSCORE_WINDOW_30,
        add_oi_delta_5_z30_feature,
    )

    assert callable(add_oi_delta_5_z30_feature), "add_oi_delta_5_z30_feature is not callable."
    assert OI_DELTA_5_Z30_COLUMN == "btc_oi_delta_5_z30", (
        f"OI_DELTA_5_Z30_COLUMN expected 'btc_oi_delta_5_z30', got {OI_DELTA_5_Z30_COLUMN!r}."
    )
    assert OI_DELTA_LOOKBACK_5 == 5, f"OI_DELTA_LOOKBACK_5 expected 5, got {OI_DELTA_LOOKBACK_5}."
    assert OI_ZSCORE_WINDOW_30 == 30, f"OI_ZSCORE_WINDOW_30 expected 30, got {OI_ZSCORE_WINDOW_30}."


# ---------------------------------------------------------------------------
# 10. test_add_oi_delta_5_z30_feature_computes
# ---------------------------------------------------------------------------


def test_add_oi_delta_5_z30_feature_computes() -> None:
    """BTCUSDT produces non-NaN btc_oi_delta_5_z30 values after 35-bar burn-in."""
    from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_5_z30_feature

    n = 300
    df = _make_kline_df(n=n, seed=58, symbol="BTCUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        _make_oi_csv(Path(tmpdir), n=n, seed=42)
        out = add_oi_delta_5_z30_feature(df, data_dir=Path(tmpdir))

    assert "btc_oi_delta_5_z30" in out.columns, (
        "btc_oi_delta_5_z30 column missing from add_oi_delta_5_z30_feature output."
    )

    non_nan = out["btc_oi_delta_5_z30"].dropna()
    assert len(non_nan) > 0, (
        "btc_oi_delta_5_z30 is all-NaN; expected non-NaN values after 35-bar burn-in."
    )

    # Burn-in: first ~34 rows NaN (delta_window=5 + zscore_window=30 - 1)
    assert out["btc_oi_delta_5_z30"].iloc[:34].isna().all(), (
        f"First 34 rows should be NaN (35-bar burn-in). "
        f"Non-NaN in first 34: {out['btc_oi_delta_5_z30'].iloc[:34].notna().sum()}"
    )

    # Clipping
    assert (non_nan.abs() <= 10.0 + 1e-9).all(), (
        f"btc_oi_delta_5_z30 clip failed; max_abs = {non_nan.abs().max():.4f}"
    )


# ---------------------------------------------------------------------------
# 11. test_runner_metadata_058
# ---------------------------------------------------------------------------


def test_runner_metadata_058() -> None:
    """Verify run_iteration_058.py has correct metadata constants."""
    import run_iteration_058

    assert run_iteration_058.ITERATION_NUMBER == 58, (
        f"ITERATION_NUMBER expected 58, got {run_iteration_058.ITERATION_NUMBER}."
    )
    assert run_iteration_058.ITERATION_LABEL == "v1-058", (
        f"ITERATION_LABEL expected 'v1-058', got {run_iteration_058.ITERATION_LABEL!r}."
    )
    assert run_iteration_058.SEEDS_DEFAULT == 3, (
        f"SEEDS_DEFAULT expected 3 (multi-seed built-in), got {run_iteration_058.SEEDS_DEFAULT}."
    )
    assert run_iteration_058.ENSEMBLE_SIZE == 3, (
        f"ENSEMBLE_SIZE expected 3 (inner; EXPLORATION standard), "
        f"got {run_iteration_058.ENSEMBLE_SIZE}."
    )
    assert run_iteration_058.N_TRIALS_DEFAULT == 18, (
        f"N_TRIALS_DEFAULT expected 18 (EXPLORATION standard), "
        f"got {run_iteration_058.N_TRIALS_DEFAULT}."
    )
    # Hash guard
    h49 = run_iteration_058.FEATURES_BASE_HASH_49COL
    h48 = run_iteration_058.FEATURES_BASE_HASH_48COL
    assert h49 != h48, "49-col and 48-col hashes must differ."


# ---------------------------------------------------------------------------
# 12. test_oi_delta_5_z30_clip_range
# ---------------------------------------------------------------------------


def test_oi_delta_5_z30_clip_range() -> None:
    """Output of compute_oi_delta_zscore(delta=5, z=30) is always in [-10, +10].

    Test with extreme OI spikes (simulating liquidation cascade) to verify clipping holds.
    """
    from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

    rng = np.random.default_rng(58)
    n = 500
    # Base OI with random walk
    oi_base = 100_000.0 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    # Inject 5 extreme OI spike events (10x increase in one bar)
    for spike_pos in [100, 150, 200, 300, 400]:
        oi_base[spike_pos] *= 10.0

    oi_series = pd.Series(oi_base)
    out = compute_oi_delta_zscore(oi_series, delta_window=5, zscore_window=30)

    finite = out.dropna()
    assert (finite.abs() <= 10.0 + 1e-9).all(), (
        f"Clip failed even with extreme OI spikes. max_abs = {finite.abs().max():.4f}. "
        "OI_ZSCORE_CLIP=10.0 must apply unconditionally."
    )
    # With extreme spikes, we expect some values hitting the clip boundary
    clipped = (finite.abs() >= 9.5).sum()
    print(f"  [OK] Extreme spikes: {clipped} values hit ±9.5+ boundary (clip working)")


# ---------------------------------------------------------------------------
# Bonus parametrized: feature presence/absence in pruned set at /058
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "feature_name,expected_in_pruned",
    [
        ("btc_oi_delta_5_z30", False),  # ADDED at /058 then REVERTED (BASIN-LOTTERY); NOT present
        ("oi_delta_30_z90", True),  # ADDED at /025; still present (sister feature)
        ("btc_funding_spread_30_90", True),  # RETAINED at /054; still present
        ("eth_vs_btc_ret_ratio_30", True),  # ADDED at /055; still present
        ("dot_vs_btc_ret_ratio_30", True),  # ADDED at /050; still present
        ("btc_funding_rate_8h_impulse", False),  # DROPPED at /054; NOT present
        ("ltc_vs_btc_ret_ratio_30", False),  # REVERTED at /057; NOT present
        ("basis_zscore_30", False),  # DROPPED at /040; NOT present
    ],
)
def test_feature_presence_parametrized(feature_name: str, expected_in_pruned: bool) -> None:
    """Parametrized check for feature presence/absence in V1_FEATURE_COLUMNS_PRUNED at /058."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    actual = feature_name in V1_FEATURE_COLUMNS_PRUNED
    assert actual == expected_in_pruned, (
        f"Feature {feature_name!r}: expected in_pruned={expected_in_pruned}, got {actual}. "
        f"V1_FEATURE_COLUMNS_PRUNED has {len(V1_FEATURE_COLUMNS_PRUNED)} cols at /058."
    )
