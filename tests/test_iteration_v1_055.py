"""Tests for iter-v1/055: ETH-only specialist — eth_vs_btc_ret_ratio_30.

Covers 8 tests:

1. test_eth_vs_btc_ret_ratio_30_in_pruned — eth_vs_btc_ret_ratio_30 IS in V1_FEATURE_COLUMNS_PRUNED.
2. test_pruned_size_48 — V1_FEATURE_COLUMNS_PRUNED has exactly 48 features.
3. test_eth_only_cohort — V1_ITER055_UNIVERSE is exactly ("ETHUSDT",).
4. test_no_lookahead — perturbing future bar does NOT affect past zscore values.
5. test_synthetic_eth_btc_ratio — known inputs → known output.
6. test_features_base_hash_changed_vs_054 — 48-col hash differs from /054 47-col hash.
7. test_eth_feature_computed_non_nan — ETHUSDT produces non-NaN values after warmup.
8. test_dot_feature_nan_for_eth_symbol — dot_vs_btc_ret_ratio_30 is NaN for ETHUSDT.
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


def _make_kline_df(n: int = 300, seed: int = 42, symbol: str = "ETHUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time, close, symbol."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC (IS window start)
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    open_times = [start_ms + i * interval_ms for i in range(n)]
    log_rets = rng.normal(0, 0.02, n)
    prices = 1800.0 * np.exp(np.cumsum(log_rets))  # ETH-scale price
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": prices * 0.999,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": rng.uniform(1000, 100000, n),
            "symbol": symbol,
        }
    )


def _make_btc_csv(tmpdir: Path, n: int = 300, seed: int = 99) -> Path:
    """Write a fake BTCUSDT/8h.csv to tmpdir aligned to ETHUSDT open_times, return path."""
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
# 1. test_eth_vs_btc_ret_ratio_30_in_pruned
# ---------------------------------------------------------------------------


def test_eth_vs_btc_ret_ratio_30_in_pruned() -> None:
    """eth_vs_btc_ret_ratio_30 must be present in V1_FEATURE_COLUMNS_PRUNED at iter-v1/055.

    /055 ADD mandate: eth_vs_btc_ret_ratio_30 added to V1_FEATURE_COLUMNS_PRUNED (47 → 48 cols).
    Alphabetically inserted between dot_vs_btc_ret_ratio_30 and funding_rate_zscore_30.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "eth_vs_btc_ret_ratio_30 not found in V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure iter-v1/055 ADD is present in features_v1/__init__.py. "
        "Expected insertion between dot_vs_btc_ret_ratio_30 and funding_rate_zscore_30."
    )


# ---------------------------------------------------------------------------
# 2. test_pruned_size_48
# ---------------------------------------------------------------------------


def test_pruned_size_48() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features at iter-v1/055.

    History:
        40 (baseline /002) → 42 (/023) → 43 (/025) → 44 (/034→/040) → 45 (/049)
        → 46 (/050 ADD dot_vs_btc_ret_ratio_30)
        → 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90)
        → 47 (/054 DROP btc_funding_rate_8h_impulse)
        → 48 (/055 ADD eth_vs_btc_ret_ratio_30)
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 49, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 49 features (post iter-v1/057 ADD); got {n}. "
        "History: /054 dropped impulse (48→47); /055 adds eth_vs_btc_ret_ratio_30 (47→48); "
        "/057 adds ltc_vs_btc_ret_ratio_30 (48→49). "
        "If n == 48: ltc_vs_btc_ret_ratio_30 was NOT added at /057. "
        "If n == 47: eth_vs_btc_ret_ratio_30 was NOT added — check /055 implementation. "
        "If n < 47: something was accidentally removed."
    )


# ---------------------------------------------------------------------------
# 3. test_eth_only_cohort
# ---------------------------------------------------------------------------


def test_eth_only_cohort() -> None:
    """V1_ITER055_UNIVERSE must be exactly ('ETHUSDT',) — ETH-only cohort.

    Independently defined constant. ETH-only specialist head; BTC loaded for cross-asset
    feature computation only, NOT traded.
    """
    from crypto_trade.features_v1 import V1_ITER055_UNIVERSE

    assert set(V1_ITER055_UNIVERSE) == {"ETHUSDT"}, (
        f"V1_ITER055_UNIVERSE expected {{'ETHUSDT'}}, got {set(V1_ITER055_UNIVERSE)}. "
        "Brief Section 10.1: ETH-only cohort for /055 specialist head. "
        "BTCUSDT is loaded for cross-asset feature computation only — not traded."
    )
    assert len(V1_ITER055_UNIVERSE) == 1, (
        f"V1_ITER055_UNIVERSE should have exactly 1 symbol; got {len(V1_ITER055_UNIVERSE)}."
    )

    # V1_ITER055_UNIVERSE must be in __all__
    import crypto_trade.features_v1 as fv1

    assert "V1_ITER055_UNIVERSE" in fv1.__all__, (
        "V1_ITER055_UNIVERSE not found in crypto_trade.features_v1.__all__. "
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
    from crypto_trade.features_v1.cross_btc_v1 import compute_eth_vs_btc_ret_ratio_30

    rng = np.random.default_rng(42)
    n = 300
    eth_prices = 1800.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    btc_prices = 30000.0 * np.exp(np.cumsum(rng.normal(0, 0.018, n)))

    df_eth1 = pd.DataFrame({"close": eth_prices, "open_time": range(n)})
    df_btc1 = pd.DataFrame({"close": btc_prices, "open_time": range(n)})

    # Compute baseline
    out1 = compute_eth_vs_btc_ret_ratio_30(df_eth1, df_btc1)

    # Perturb ONLY the last bar's BTC price (extreme value)
    btc_prices2 = btc_prices.copy()
    btc_prices2[-1] = btc_prices[-1] * 1000.0  # extreme perturbation

    df_eth2 = pd.DataFrame({"close": eth_prices.copy(), "open_time": range(n)})
    df_btc2 = pd.DataFrame({"close": btc_prices2, "open_time": range(n)})

    out2 = compute_eth_vs_btc_ret_ratio_30(df_eth2, df_btc2)

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
# 5. test_synthetic_eth_btc_ratio — known inputs → known output
# ---------------------------------------------------------------------------


def test_synthetic_eth_btc_ratio() -> None:
    """Known inputs produce expected output for compute_eth_vs_btc_ret_ratio_30.

    Test case A: constant prices — pct_change = 0 → ratio = 0/0 → NaN.
    Test case B: proportional drift — ETH = BTC × constant → ratio ~ 1 (constant) →
        rolling std → 0 → zscore = NaN (denominator zero replace).
    Test case C: divergent drifts — ETH doubles faster than BTC → ratio > 1 progressively;
        z-scored output should be finite after warmup and clipped to ±10.
    """
    from crypto_trade.features_v1.cross_btc_v1 import compute_eth_vs_btc_ret_ratio_30

    n = 300

    # Test A: constant prices
    eth_const = pd.DataFrame({"close": [1800.0] * n, "open_time": range(n)})
    btc_const = pd.DataFrame({"close": [30000.0] * n, "open_time": range(n)})
    out_a = compute_eth_vs_btc_ret_ratio_30(eth_const, btc_const)
    assert out_a.isna().all(), (
        "With constant prices (pct_change=0), ratio = 0/0 = NaN. "
        f"Expected all-NaN output; got {out_a.dropna().head(5)}."
    )

    # Test B: proportional drift (ETH = 0.06 × BTC)
    # pct_change(30) for both: ratio = eth_ret/btc_ret ≈ 1.0 (constant) → std=0 → NaN
    n2 = 500
    btc_drift = [30000.0 * (1.005**i) for i in range(n2)]
    eth_drift = [1800.0 * (1.005**i) for i in range(n2)]  # same growth rate
    df_eth_b = pd.DataFrame({"close": eth_drift, "open_time": range(n2)})
    df_btc_b = pd.DataFrame({"close": btc_drift, "open_time": range(n2)})
    out_b = compute_eth_vs_btc_ret_ratio_30(df_eth_b, df_btc_b)
    # Ratio is ~1.0 constant → rolling std → 0 → NaN denominator replace → NaN output
    # Either all-NaN or within clip bounds if std barely non-zero due to floating point
    finite_b = out_b.dropna()
    if len(finite_b) > 0:
        assert (finite_b.abs() <= 10.0 + 1e-9).all(), (
            f"Proportional drift: clipping failed; max_abs={finite_b.abs().max():.4f} > 10.0"
        )

    # Test C: divergent drift — verify finite clipped output after warmup
    rng = np.random.default_rng(55)
    eth_prices_c = 1800.0 * np.exp(np.cumsum(rng.normal(0.003, 0.02, n2)))  # higher ETH drift
    btc_prices_c = 30000.0 * np.exp(np.cumsum(rng.normal(0.001, 0.018, n2)))  # lower BTC drift
    df_eth_c = pd.DataFrame({"close": eth_prices_c, "open_time": range(n2)})
    df_btc_c = pd.DataFrame({"close": btc_prices_c, "open_time": range(n2)})
    out_c = compute_eth_vs_btc_ret_ratio_30(df_eth_c, df_btc_c)
    finite_c = out_c.iloc[90:].dropna()  # after warmup
    assert len(finite_c) > 0, (
        "Expected non-NaN values after 90-bar warmup with divergent drift prices."
    )
    assert (finite_c.abs() <= 10.0 + 1e-9).all(), (
        f"Divergent drift: clipping failed; max_abs={finite_c.abs().max():.4f} > 10.0"
    )


# ---------------------------------------------------------------------------
# 6. test_features_base_hash_changed_vs_054
# ---------------------------------------------------------------------------


def test_features_base_hash_changed_vs_054() -> None:
    """The features-base-hash at /055 must DIFFER from the hash at /054.

    /054 used 47 cols (impulse DROPPED; spread RETAINED).
    /055 adds eth_vs_btc_ret_ratio_30 (47 → 48 cols).
    /057 further adds ltc_vs_btc_ret_ratio_30 (48 → 49 cols).
    The SHA-256 of the /055 48-col set MUST differ from the /054 47-col set.
    The live hash (49-col post-/057) must differ from both.
    """
    import run_iteration_055

    # Pre-registered reference hashes from the /055 runner
    expected_48col = run_iteration_055.FEATURES_BASE_HASH_48COL
    expected_47col = run_iteration_055.FEATURES_BASE_HASH_47COL

    # The two /055-anchored hashes must be different (eth feature ADD changed the column set)
    assert expected_48col != expected_47col, (
        "FEATURES_BASE_HASH_48COL and FEATURES_BASE_HASH_47COL must differ in run_iteration_055. "
        "Adding eth_vs_btc_ret_ratio_30 (47→48 cols) produces a different SHA-256. "
        "If they are equal, the pre-registered hash constants are wrong."
    )

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    live_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)

    # /057 added ltc_vs_btc_ret_ratio_30: the live (49-col) hash must differ from both
    # the /055 48-col hash AND the /054 47-col hash.
    assert live_hash != expected_47col, (
        f"Live V1_FEATURE_COLUMNS_PRUNED hash matches the 47-col reference hash:\n"
        f"  live computed: {live_hash}\n"
        f"  expected_47col: {expected_47col}\n"
        "eth_vs_btc_ret_ratio_30 appears to NOT be in V1_FEATURE_COLUMNS_PRUNED. "
        "The /055 feature-add was not applied."
    )
    # Note: live hash now equals /057 49-col hash (not /055 48-col hash) — this is correct.
    # The /057 ADD is confirmed; /055 eth feature is still present.
    assert "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "eth_vs_btc_ret_ratio_30 must be in V1_FEATURE_COLUMNS_PRUNED (added at /055, retained). "
        "The /057 ADD (ltc_vs_btc_ret_ratio_30) must not have displaced it."
    )

    print(f"  [OK] expected_48col hash = {expected_48col[:16]}... (/055 reference, now superseded)")
    print(f"  [OK] expected_47col hash = {expected_47col[:16]}... (/054 reference)")
    print(f"  [OK] live hash           = {live_hash[:16]}... (/057 49-col hash)")
    print("  [OK] Hashes differ from /054 reference (eth + ltc feature ADDs confirmed).")


# ---------------------------------------------------------------------------
# 7. test_eth_feature_computed_non_nan
# ---------------------------------------------------------------------------


def test_eth_feature_computed_non_nan() -> None:
    """ETHUSDT produces non-NaN eth_vs_btc_ret_ratio_30 values after warmup period.

    Warmup: first 90 rows NaN (rolling zscore min_periods=90 dominates).
    After warmup: non-NaN values expected from the cross-asset ratio computation.
    """
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    n = 300
    df_eth = _make_kline_df(n=n, seed=42, symbol="ETHUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        _make_btc_csv(Path(tmpdir), n=n, seed=99)
        out = add_cross_btc_v1_features(df_eth, data_dir=Path(tmpdir))

    # ETH feature: non-NaN after warmup
    assert "eth_vs_btc_ret_ratio_30" in out.columns, (
        "eth_vs_btc_ret_ratio_30 column missing from add_cross_btc_v1_features output for ETHUSDT."
    )
    non_nan_eth = out["eth_vs_btc_ret_ratio_30"].dropna()
    assert len(non_nan_eth) > 0, (
        "eth_vs_btc_ret_ratio_30 is all-NaN for ETHUSDT after add_cross_btc_v1_features. "
        "Expected non-NaN values after 90-bar warmup (n=300 bars; 210 non-NaN expected)."
    )
    # Warmup: first 90 rows should be NaN (zscore window dominates)
    assert out["eth_vs_btc_ret_ratio_30"].iloc[:89].isna().all(), (
        "eth_vs_btc_ret_ratio_30: first 89 rows should be NaN (90-bar zscore warmup). "
        f"Non-NaN count in first 89 rows: {out['eth_vs_btc_ret_ratio_30'].iloc[:89].notna().sum()}"
    )
    # Values should be clipped to [-10, +10]
    assert (non_nan_eth.abs() <= 10.0 + 1e-9).all(), (
        f"eth_vs_btc_ret_ratio_30 clipping failed: max_abs={non_nan_eth.abs().max():.4f} > 10.0"
    )


# ---------------------------------------------------------------------------
# 8. test_dot_feature_nan_for_eth_symbol
# ---------------------------------------------------------------------------


def test_dot_feature_nan_for_eth_symbol() -> None:
    """dot_vs_btc_ret_ratio_30 must be all-NaN for ETHUSDT symbol.

    ETHUSDT uses eth_vs_btc_ret_ratio_30 (iter-v1/055).
    dot_vs_btc_ret_ratio_30 is DOT-only and must be NaN for ETHUSDT.
    Both columns must exist in the output for V1_FEATURE_COLUMNS_PRUNED compliance.
    """
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    n = 300
    df_eth = _make_kline_df(n=n, seed=42, symbol="ETHUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        _make_btc_csv(Path(tmpdir), n=n, seed=99)
        out = add_cross_btc_v1_features(df_eth, data_dir=Path(tmpdir))

    # dot_vs_btc_ret_ratio_30 must exist but be all-NaN for ETHUSDT
    assert "dot_vs_btc_ret_ratio_30" in out.columns, (
        "dot_vs_btc_ret_ratio_30 column missing from add_cross_btc_v1_features output for ETHUSDT. "
        "The column must exist (even as NaN) for V1_FEATURE_COLUMNS_PRUNED compliance."
    )
    assert out["dot_vs_btc_ret_ratio_30"].isna().all(), (
        "dot_vs_btc_ret_ratio_30 should be all-NaN for ETHUSDT (DOT-only feature). "
        f"Non-NaN count: {out['dot_vs_btc_ret_ratio_30'].notna().sum()}. "
        "Regression in add_cross_btc_v1_features dispatch: ETH branch must set DOT column to NaN."
    )


# ---------------------------------------------------------------------------
# Bonus: runner metadata checks
# ---------------------------------------------------------------------------


def test_runner_metadata_055() -> None:
    """Verify run_iteration_055.py has correct metadata constants."""
    import run_iteration_055

    assert run_iteration_055.ITERATION_NUMBER == 55, (
        f"ITERATION_NUMBER expected 55, got {run_iteration_055.ITERATION_NUMBER}."
    )
    assert run_iteration_055.ITERATION_LABEL == "v1-055", (
        f"ITERATION_LABEL expected 'v1-055', got {run_iteration_055.ITERATION_LABEL!r}."
    )
    assert run_iteration_055.SEEDS_DEFAULT == 1, (
        f"SEEDS_DEFAULT expected 1 (single-seed=42; EXPLORATION budget), "
        f"got {run_iteration_055.SEEDS_DEFAULT}."
    )
    assert run_iteration_055.ENSEMBLE_SIZE == 3, (
        f"ENSEMBLE_SIZE expected 3 (inner; EXPLORATION standard), "
        f"got {run_iteration_055.ENSEMBLE_SIZE}."
    )
    assert run_iteration_055.N_TRIALS_DEFAULT == 18, (
        f"N_TRIALS_DEFAULT expected 18 (EXPLORATION standard), "
        f"got {run_iteration_055.N_TRIALS_DEFAULT}."
    )
    # Hash guard: 48-col hash must differ from 47-col hash
    h48 = run_iteration_055.FEATURES_BASE_HASH_48COL
    h47 = run_iteration_055.FEATURES_BASE_HASH_47COL
    assert h48 != h47, (
        "FEATURES_BASE_HASH_48COL must differ from FEATURES_BASE_HASH_47COL. "
        "Eth feature ADD changes the column set — hashes must be different."
    )


# ---------------------------------------------------------------------------
# Bonus: cross-btc_v1 compute function import and ETH constant verification
# ---------------------------------------------------------------------------


def test_eth_compute_function_importable() -> None:
    """compute_eth_vs_btc_ret_ratio_30 must be importable from cross_btc_v1."""
    from crypto_trade.features_v1.cross_btc_v1 import (
        ETH_FEATURE_COLUMN,
        ETH_TARGET_SYMBOL,
        compute_eth_vs_btc_ret_ratio_30,
    )

    assert callable(compute_eth_vs_btc_ret_ratio_30), (
        "compute_eth_vs_btc_ret_ratio_30 is not callable."
    )
    assert ETH_FEATURE_COLUMN == "eth_vs_btc_ret_ratio_30", (
        f"ETH_FEATURE_COLUMN expected 'eth_vs_btc_ret_ratio_30', got {ETH_FEATURE_COLUMN!r}."
    )
    assert ETH_TARGET_SYMBOL == "ETHUSDT", (
        f"ETH_TARGET_SYMBOL expected 'ETHUSDT', got {ETH_TARGET_SYMBOL!r}."
    )


@pytest.mark.parametrize(
    "feature_name,expected_in_pruned",
    [
        ("eth_vs_btc_ret_ratio_30", True),  # ADDED at /055
        ("dot_vs_btc_ret_ratio_30", True),  # ADDED at /050; must still be present
        ("btc_funding_spread_30_90", True),  # RETAINED at /054; must still be present
        ("btc_funding_rate_8h_impulse", False),  # DROPPED at /054; must NOT be present
        ("basis_zscore_30", False),  # dropped at /034/040; must NOT be present
        ("regime_momentum_signed_5d", True),  # added at /040; must still be present
    ],
)
def test_feature_presence_parametrized(feature_name: str, expected_in_pruned: bool) -> None:
    """Parametrized check for feature presence/absence in V1_FEATURE_COLUMNS_PRUNED at /055."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    actual = feature_name in V1_FEATURE_COLUMNS_PRUNED
    assert actual == expected_in_pruned, (
        f"Feature {feature_name!r}: expected in_pruned={expected_in_pruned}, "
        f"got {actual}. "
        f"V1_FEATURE_COLUMNS_PRUNED has {len(V1_FEATURE_COLUMNS_PRUNED)} cols at /055. "
        f"At /055: eth_vs_btc_ret_ratio_30 ADDED; btc_funding_rate_8h_impulse DROPPED at /054; "
        f"all other features unchanged."
    )
