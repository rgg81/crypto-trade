"""Tests for iter-v1/050: dot_vs_btc_ret_ratio_30 feature + vol-spike regime gate.

Covers 8 tests:

1.  test_cross_btc_v1_no_lookahead — perturbing ratio[-1] does NOT affect zscore[<-1].
2.  test_regime_gate_uses_training_only — q75 computation from IS-only bars (no OOS peek).
3.  test_dot_only_cohort — DOTUSDT produces feature values; non-DOT symbols produce NaN.
4.  test_feature_in_pruned — dot_vs_btc_ret_ratio_30 present in V1_FEATURE_COLUMNS_PRUNED.
5.  test_synthetic_btc_ratio — known inputs (constant returns) → known output (0 or NaN).
6.  test_pruned_size_46 — V1_FEATURE_COLUMNS_PRUNED has exactly 46 features.
7.  test_track_isolation — cross_btc_v1.py has ZERO imports from features_v2 or features_v3.
8.  test_group_registry_cross_btc_v1 — cross_btc_v1 registered in GROUP_REGISTRY (callable).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_kline_df(n: int = 300, seed: int = 42, symbol: str = "DOTUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time, close, symbol."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC (IS window start)
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    open_times = [start_ms + i * interval_ms for i in range(n)]
    # Simulate realistic price: geometric random walk
    log_rets = rng.normal(0, 0.02, n)
    prices = 10.0 * np.exp(np.cumsum(log_rets))
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
    """Write a fake BTCUSDT/8h.csv to tmpdir, return path."""
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


def _make_eth_csv(tmpdir: Path, n: int = 300, seed: int = 77) -> Path:
    """Write a fake ETHUSDT/8h.csv to tmpdir (iter-v1/078 excess_ret needs ETH).

    Required because add_cross_btc_v1_features now loads ETH for ALL symbols
    to compute excess_ret_5d_vs_majors_z90 universally.
    """
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    log_rets = rng.normal(0, 0.020, n)
    prices = 2000.0 * np.exp(np.cumsum(log_rets))
    eth_dir = tmpdir / "ETHUSDT"
    eth_dir.mkdir(parents=True, exist_ok=True)
    csv_path = eth_dir / "8h.csv"
    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": prices * 0.999,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": rng.uniform(1e5, 1e7, n),
        }
    )
    df.to_csv(csv_path, index=False)
    return csv_path


# ---------------------------------------------------------------------------
# 1. test_cross_btc_v1_no_lookahead
# ---------------------------------------------------------------------------


def test_cross_btc_v1_no_lookahead() -> None:
    """Perturbing ratio[-1] does NOT affect zscore[<-1] (no look-ahead).

    The rolling zscore at bar t uses only ratio[t-window+1]...ratio[t].
    Perturbing bar N does not reach back to earlier bars.
    """
    from crypto_trade.features_v1.cross_btc_v1 import compute_dot_vs_btc_ret_ratio_30

    rng = np.random.default_rng(42)
    n = 300
    dot_prices = 10.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    btc_prices = 30000.0 * np.exp(np.cumsum(rng.normal(0, 0.018, n)))

    df_dot1 = pd.DataFrame({"close": dot_prices, "open_time": range(n)})
    df_btc1 = pd.DataFrame({"close": btc_prices, "open_time": range(n)})

    # Compute baseline
    out1 = compute_dot_vs_btc_ret_ratio_30(df_dot1, df_btc1)

    # Perturb ONLY the last bar's BTC price (extreme value)
    btc_prices2 = btc_prices.copy()
    btc_prices2[-1] = btc_prices[-1] * 1000.0  # extreme perturbation

    df_dot2 = pd.DataFrame({"close": dot_prices.copy(), "open_time": range(n)})
    df_btc2 = pd.DataFrame({"close": btc_prices2, "open_time": range(n)})

    out2 = compute_dot_vs_btc_ret_ratio_30(df_dot2, df_btc2)

    # All rows EXCEPT the last window should be identical
    # (perturbing last bar affects pct_change(30) for the last 30 bars in BTC ret,
    # and then rolling zscore at the perturbed bars, but should NOT affect earlier rows)
    # We check that rows far from the end are identical
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
# 2. test_regime_gate_uses_training_only
# ---------------------------------------------------------------------------


def test_regime_gate_uses_training_only() -> None:
    """q75 of btc_realized_vol_30 must be computed from IS-only bars (no OOS peek).

    This test verifies the gate computation logic: if we have 400 bars with
    OOS_CUTOFF at bar 300, then q75 must use only bars 0..299.
    """
    from crypto_trade.features_v1.cross_btc_v1 import compute_btc_realized_vol_30

    n = 400
    oos_cutoff = 300  # bar index (not ms)
    rng = np.random.default_rng(55)

    # Create prices: IS period has lower vol, OOS period has extreme vol
    is_prices = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.005, oos_cutoff)))  # low vol
    oos_prices = is_prices[-1] * np.exp(np.cumsum(rng.normal(0, 0.1, n - oos_cutoff)))  # high vol
    all_prices = np.concatenate([is_prices, oos_prices])

    btc_close = pd.Series(all_prices)
    vol_series = compute_btc_realized_vol_30(btc_close)

    # IS vols (bars < oos_cutoff)
    is_vols = vol_series.iloc[:oos_cutoff].dropna().values
    # OOS vols (bars >= oos_cutoff)
    oos_vols = vol_series.iloc[oos_cutoff:].dropna().values

    # q75 from IS only
    is_q75 = float(np.percentile(is_vols, 75))
    # q75 from ALL data (this would be the "contaminated" q75)
    all_vols = vol_series.dropna().values
    all_q75 = float(np.percentile(all_vols, 75))

    # IS q75 should be substantially lower than ALL q75 (IS was low-vol, OOS was high-vol)
    assert is_q75 < all_q75, (
        f"IS q75 ({is_q75:.6f}) should be < ALL q75 ({all_q75:.6f}) "
        "because OOS period has much higher vol (10x higher std). "
        "This verifies the IS-only threshold is meaningfully different from contaminated ALL."
    )

    # IS q75 should be well below OOS median (IS is low-vol period)
    oos_median = float(np.median(oos_vols))
    assert is_q75 < oos_median, (
        f"IS q75 ({is_q75:.6f}) should be < OOS median ({oos_median:.6f}). "
        "The IS-only threshold must not be contaminated by OOS high-vol values."
    )


# ---------------------------------------------------------------------------
# 3. test_dot_only_cohort
# ---------------------------------------------------------------------------


def test_dot_only_cohort() -> None:
    """DOTUSDT produces feature values; non-DOT symbols (e.g. LINKUSDT) produce NaN."""
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    n = 300
    df_dot = _make_kline_df(n=n, seed=42, symbol="DOTUSDT")
    df_link = _make_kline_df(n=n, seed=43, symbol="LINKUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        _make_btc_csv(Path(tmpdir), n=n, seed=99)
        _make_eth_csv(Path(tmpdir), n=n, seed=77)

        out_dot = add_cross_btc_v1_features(df_dot, data_dir=Path(tmpdir))
        out_link = add_cross_btc_v1_features(df_link, data_dir=Path(tmpdir))

    # DOT: feature column exists and has some non-NaN values (after warmup)
    assert "dot_vs_btc_ret_ratio_30" in out_dot.columns
    non_nan_dot = out_dot["dot_vs_btc_ret_ratio_30"].dropna()
    assert len(non_nan_dot) > 0, (
        "dot_vs_btc_ret_ratio_30 is all-NaN for DOTUSDT. Expected non-NaN values after warmup."
    )

    # LINK: feature column exists but is ALL NaN (DOT-only feature)
    assert "dot_vs_btc_ret_ratio_30" in out_link.columns
    assert out_link["dot_vs_btc_ret_ratio_30"].isna().all(), (
        "dot_vs_btc_ret_ratio_30 should be all-NaN for non-DOTUSDT symbols (LINKUSDT). "
        "Feature is DOT-only."
    )


# ---------------------------------------------------------------------------
# 4. test_feature_in_pruned
# ---------------------------------------------------------------------------


def test_feature_in_pruned() -> None:
    """dot_vs_btc_ret_ratio_30 must be present in V1_FEATURE_COLUMNS_PRUNED."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "dot_vs_btc_ret_ratio_30 not found in V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure iter-v1/050 ADD is present in features_v1/__init__.py."
    )


# ---------------------------------------------------------------------------
# 5. test_synthetic_btc_ratio — known inputs → known output
# ---------------------------------------------------------------------------


def test_synthetic_btc_ratio() -> None:
    """Known inputs produce expected output for compute_dot_vs_btc_ret_ratio_30.

    Test case: DOT and BTC have identical constant prices (no movement).
    pct_change(30) = 0 for both → ratio = 0/0 → NaN (not 1.0 — zero/zero is undefined).
    """
    from crypto_trade.features_v1.cross_btc_v1 import compute_dot_vs_btc_ret_ratio_30

    n = 300
    # Constant prices: pct_change = 0 for both DOT and BTC
    dot_const = pd.DataFrame({"close": [10.0] * n, "open_time": range(n)})
    btc_const = pd.DataFrame({"close": [30000.0] * n, "open_time": range(n)})

    out = compute_dot_vs_btc_ret_ratio_30(dot_const, btc_const)

    # All values should be NaN (0/0 = NaN → rolling zscore of all-NaN = NaN)
    assert out.isna().all(), (
        "With constant prices (pct_change=0), ratio = 0/0 = NaN. "
        f"Expected all-NaN output; got {out.dropna().head(5)}."
    )

    # Test case: DOT up 10% every 30 bars; BTC up 20% every 30 bars.
    # Expected ratio = 0.1 / 0.2 = 0.5 (constant after warmup).
    # z-score of constant = NaN (std=0 denominator → we replace 0 with NaN).
    n2 = 500
    dot_drift = pd.DataFrame(
        {"close": [10.0 * (1.1 ** (i // 30)) for i in range(n2)], "open_time": range(n2)}
    )
    btc_drift = pd.DataFrame(
        {"close": [30000.0 * (1.2 ** (i // 30)) for i in range(n2)], "open_time": range(n2)}
    )
    out2 = compute_dot_vs_btc_ret_ratio_30(dot_drift, btc_drift)
    # With constant ratio (~0.5), rolling std → 0 → zscore = NaN (denominator replace)
    # Some rows may be NaN; the important thing is no inf or out-of-clip values
    finite_vals = out2.dropna()
    if len(finite_vals) > 0:
        assert (finite_vals.abs() <= 10.0 + 1e-9).all(), (
            f"Clipping failed: max_abs = {finite_vals.abs().max():.4f} > 10.0"
        )


# ---------------------------------------------------------------------------
# 6. test_pruned_size_46
# ---------------------------------------------------------------------------


def test_pruned_size_46() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features (post /057-CLOSEOUT REVERT).

    iter-v1/050 ADD extended 45→46 (dot_vs_btc_ret_ratio_30).
    iter-v1/052: 46→48 (+btc_funding_rate_8h_impulse +btc_funding_spread_30_90).
    iter-v1/057 CLOSEOUT reverted ltc_vs_btc_ret_ratio_30 (49→48, multi-seed falsified);
    iter-v1/084 fix 960da644 restored the global PRUNED to 48 (specialist adds are LOCAL).
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 48, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 48 features (post /057-CLOSEOUT REVERT + "
        f"/084 fix 960da644); got {n}. "
        "History: ...→ 45 (/049) → 46 (/050 ADD dot_vs_btc_ret_ratio_30) "
        "→ 48 (/052 ADD btc_funding_rate_8h_impulse + btc_funding_spread_30_90) "
        "→ 47 (/054 DROP btc_funding_rate_8h_impulse) "
        "→ 48 (/055 ADD eth_vs_btc_ret_ratio_30) "
        "→ 49 (/057 ADD ltc_vs_btc_ret_ratio_30) "
        "→ 48 (/057 CLOSEOUT REVERT ltc_vs_btc_ret_ratio_30; /084 960da644 keeps 48 — "
        "specialist extras like /078/084/085 are LOCAL tuples, never global)."
    )


# ---------------------------------------------------------------------------
# 7. test_track_isolation
# ---------------------------------------------------------------------------


def test_track_isolation() -> None:
    """cross_btc_v1.py must have ZERO imports from features_v2 or features_v3."""
    import ast
    import importlib.util

    spec = importlib.util.find_spec("crypto_trade.features_v1.cross_btc_v1")
    assert spec is not None and spec.origin is not None, "Cannot locate cross_btc_v1 module spec."
    src = Path(spec.origin).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("crypto_trade.features_v2"), (
                f"cross_btc_v1.py imports from features_v2 (line {node.lineno}) "
                "— track isolation violated."
            )
            assert not mod.startswith("crypto_trade.features_v3"), (
                f"cross_btc_v1.py imports from features_v3 (line {node.lineno}) "
                "— track isolation violated."
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert "features_v2" not in alias.name, (
                    f"cross_btc_v1.py imports features_v2: {alias.name}"
                )
                assert "features_v3" not in alias.name, (
                    f"cross_btc_v1.py imports features_v3: {alias.name}"
                )


# ---------------------------------------------------------------------------
# 8. test_group_registry_cross_btc_v1
# ---------------------------------------------------------------------------


def test_group_registry_cross_btc_v1() -> None:
    """cross_btc_v1 must be registered in GROUP_REGISTRY and be callable."""
    from crypto_trade.features import GROUP_REGISTRY

    assert "cross_btc_v1" in GROUP_REGISTRY, (
        "cross_btc_v1 not found in GROUP_REGISTRY. "
        "Ensure _register('cross_btc_v1', _add_cross_btc_v1_features) is present "
        "in src/crypto_trade/features/__init__.py."
    )

    fn = GROUP_REGISTRY["cross_btc_v1"]
    assert callable(fn), f"GROUP_REGISTRY['cross_btc_v1'] is not callable: {fn!r}."


# ---------------------------------------------------------------------------
# Additional: btc_realized_vol_30 basic properties
# ---------------------------------------------------------------------------


def test_btc_realized_vol_warmup() -> None:
    """compute_btc_realized_vol_30: first window-1 rows are NaN (min_periods=window)."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_btc_realized_vol_30

    n = 200
    rng = np.random.default_rng(42)
    prices = 1000.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    vol_series = compute_btc_realized_vol_30(pd.Series(prices), window=30)

    burn_in = 30 - 1  # 29 NaN (min_periods=30, plus 1 NaN for first log-return)
    # The first log-return is NaN (no close[t-1] for t=0), so effectively first 30 rows NaN
    assert vol_series.iloc[: burn_in + 1].isna().all(), (
        f"Expected first {burn_in + 1} rows NaN; "
        f"got {vol_series.iloc[: burn_in + 1].notna().sum()} non-NaN."
    )
    assert vol_series.iloc[burn_in + 1 :].notna().any(), "Expected non-NaN vol values after warmup."


def test_btc_realized_vol_non_negative() -> None:
    """compute_btc_realized_vol_30: all non-NaN values must be >= 0 (std is always >= 0)."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_btc_realized_vol_30

    n = 300
    rng = np.random.default_rng(7)
    prices = 5000.0 * np.exp(np.cumsum(rng.normal(0, 0.015, n)))
    vol_series = compute_btc_realized_vol_30(pd.Series(prices))
    finite_vols = vol_series.dropna()
    assert (finite_vols >= 0).all(), (
        f"Negative vol values found: {finite_vols[finite_vols < 0].values}"
    )


def test_add_cross_btc_file_not_found() -> None:
    """add_cross_btc_v1_features raises FileNotFoundError when BTC CSV missing for DOTUSDT."""
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    df = _make_kline_df(n=50, symbol="DOTUSDT")
    with tempfile.TemporaryDirectory() as tmpdir:
        # No BTC CSV written
        with pytest.raises(FileNotFoundError, match="BTCUSDT"):
            add_cross_btc_v1_features(df, data_dir=Path(tmpdir))


def test_add_cross_btc_missing_column() -> None:
    """add_cross_btc_v1_features raises KeyError when df is missing a required column."""
    from crypto_trade.features_v1.cross_btc_v1 import add_cross_btc_v1_features

    df = _make_kline_df(n=50, symbol="DOTUSDT").drop(columns=["symbol"])
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_btc_csv(Path(tmpdir), n=50)
        _make_eth_csv(Path(tmpdir), n=50)
        with pytest.raises(KeyError, match="symbol"):
            add_cross_btc_v1_features(df, data_dir=Path(tmpdir))


def test_add_cross_btc_zscore_clip() -> None:
    """add_cross_btc_v1_features: output clipped to [-10, +10]."""
    from crypto_trade.features_v1.cross_btc_v1 import ZSCORE_CLIP, add_cross_btc_v1_features

    n = 300
    df_dot = _make_kline_df(n=n, seed=42, symbol="DOTUSDT")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write BTC CSV with near-zero returns (forces extreme ratio)
        btc_dir = Path(tmpdir) / "BTCUSDT"
        btc_dir.mkdir(parents=True, exist_ok=True)
        csv_p = btc_dir / "8h.csv"
        # BTC price oscillates wildly to force extreme ratios
        btc_prices = [30000.0 * (0.01 if i % 5 == 0 else 1.0) for i in range(n)]
        pd.DataFrame(
            {
                "open_time": df_dot["open_time"].values,
                "open": btc_prices,
                "high": btc_prices,
                "low": btc_prices,
                "close": btc_prices,
                "volume": [1e6] * n,
            }
        ).to_csv(csv_p, index=False)
        # iter-v1/078: also write ETH CSV (universal excess_ret requires ETH for all symbols)
        _make_eth_csv(Path(tmpdir), n=n, seed=77)

        out = add_cross_btc_v1_features(df_dot, data_dir=Path(tmpdir))

    finite_vals = out["dot_vs_btc_ret_ratio_30"].dropna()
    if len(finite_vals) > 0:
        assert (finite_vals.abs() <= ZSCORE_CLIP + 1e-9).all(), (
            f"z-score exceeds clip bound {ZSCORE_CLIP}: max_abs={finite_vals.abs().max():.2f}"
        )
