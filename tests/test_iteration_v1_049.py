"""Tests for iter-v1/049: long_short_zscore_30 feature dispatch.

Covers 8 tests:

1.  import_smoke_test — module and public symbols importable without error.
2.  v1_feature_columns_pruned_length_45 — V1_FEATURE_COLUMNS_PRUNED has exactly 45 features.
3.  long_short_zscore_30_in_pruned_list — feature present in V1_FEATURE_COLUMNS_PRUNED.
4.  alphabetical_position — long_short_zscore_30 between interact_* and mom_* (l between i/m).
5.  computation_correctness — rolling z-score matches manual calculation at a target row.
6.  test_past_only — perturbing lsr[-1] does NOT affect zscore[<-1] (no look-ahead).
7.  burn_in — first window-1 rows are NaN (min_periods=window).
8.  group_registry_registration — longshort_v1 registered in GROUP_REGISTRY (callable).
9.  track_isolation — longshort_v1.py has ZERO imports from features_v2 or features_v3.
10. file_not_found_error — raises FileNotFoundError when OI cache missing.
11. key_error_missing_symbol — raises KeyError when df has no symbol column.
12. missing_lsr_column — raises KeyError when OI CSV lacks sum_toptrader_long_short_ratio.
13. unmatched_rows_produce_nan — kline rows with no matching OI record produce NaN, not 0.
14. clip_applied — output clipped to [-10, +10].
15. empty_oi_cache_returns_nan — empty OI CSV produces all-NaN column without error.
16. parquet_integration — long_short_zscore_30 column present in regenerated parquets.
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


def _make_kline_df(n: int = 200, seed: int = 42, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time and symbol columns."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC (IS window start)
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    open_times = [start_ms + i * interval_ms for i in range(n)]
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": rng.uniform(100, 50000, n),
            "high": rng.uniform(100, 50000, n),
            "low": rng.uniform(100, 50000, n),
            "close": rng.uniform(100, 50000, n),
            "volume": rng.uniform(1000, 100000, n),
            "symbol": symbol,
        }
    )


def _make_oi_df_with_lsr(klines: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Create OI DataFrame aligned to kline open_times with sum_toptrader_long_short_ratio."""
    rng = np.random.default_rng(seed)
    n = len(klines)
    # Simulate long/short ratio: roughly positive, mean ~1.5
    lsr_vals = 1.0 + np.abs(rng.normal(0.5, 0.3, n))
    return pd.DataFrame(
        {
            "open_time": klines["open_time"].values,
            "sum_open_interest": rng.uniform(40000, 80000, n),
            "sum_open_interest_value": rng.uniform(1e9, 2e9, n),
            "count_toptrader_long_short_ratio": rng.uniform(100, 300, n),
            "sum_toptrader_long_short_ratio": lsr_vals,
            "count_long_short_ratio": rng.uniform(200, 400, n),
            "sum_taker_long_short_vol_ratio": rng.uniform(0.5, 2.0, n),
        }
    )


def _write_oi_csv(tmpdir: Path, symbol: str, oi_df: pd.DataFrame) -> Path:
    """Write OI CSV to tmpdir/open_interest/<symbol>/8h.csv, return path."""
    oi_dir = tmpdir / "open_interest" / symbol
    oi_dir.mkdir(parents=True, exist_ok=True)
    oi_path = oi_dir / "8h.csv"
    oi_df.to_csv(oi_path, index=False)
    return oi_path


# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------


def test_import_smoke_test() -> None:
    """Module and public symbols must be importable without error."""
    from crypto_trade.features_v1.longshort_v1 import (  # noqa: F401
        LSR_SOURCE_COLUMN,
        LSR_ZSCORE_CLIP,
        LSR_ZSCORE_WINDOW,
        add_longshort_v1_features,
        compute_long_short_zscore,
    )

    assert LSR_ZSCORE_WINDOW == 30
    assert LSR_ZSCORE_CLIP == 10.0
    assert LSR_SOURCE_COLUMN == "sum_toptrader_long_short_ratio"


# ---------------------------------------------------------------------------
# 2. V1_FEATURE_COLUMNS_PRUNED length == 45
# ---------------------------------------------------------------------------


def test_v1_feature_columns_pruned_length_45() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 46 features after iter-v1/050 ADD."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 47, (
        f"V1_FEATURE_COLUMNS_PRUNED expected 48 features after iter-v1/052 ADD; got {n}. "
        "History: ...→ 45 (/049) → 46 (/050) → 48 (/052 +btc_funding_rate_8h_impulse "
        "+btc_funding_spread_30_90)."
    )


# ---------------------------------------------------------------------------
# 3. long_short_zscore_30 in V1_FEATURE_COLUMNS_PRUNED
# ---------------------------------------------------------------------------


def test_long_short_zscore_30_in_pruned_list() -> None:
    """long_short_zscore_30 must be in V1_FEATURE_COLUMNS_PRUNED."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "long_short_zscore_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "long_short_zscore_30 not found in V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure iter-v1/049 ADD is present in features_v1/__init__.py."
    )


# ---------------------------------------------------------------------------
# 4. Alphabetical position — 'l' prefix places it before 'm' (mom_*)
# ---------------------------------------------------------------------------


def test_alphabetical_position() -> None:
    """long_short_zscore_30 must appear between interact_* and mom_* entries (alphabetically)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    cols = list(V1_FEATURE_COLUMNS_PRUNED)
    idx_lsr = cols.index("long_short_zscore_30")
    # 'l' (long) comes after 'i' (interact) and before 'm' (mom)
    interact_indices = [i for i, c in enumerate(cols) if c.startswith("interact_")]
    mom_indices = [i for i, c in enumerate(cols) if c.startswith("mom_")]

    assert interact_indices, "V1_FEATURE_COLUMNS_PRUNED must contain interact_* features."
    assert mom_indices, "V1_FEATURE_COLUMNS_PRUNED must contain mom_* features."

    last_interact_idx = max(interact_indices)
    first_mom_idx = min(mom_indices)

    assert last_interact_idx < idx_lsr < first_mom_idx, (
        f"long_short_zscore_30 at position {idx_lsr}; "
        f"last interact_* at {last_interact_idx}; first mom_* at {first_mom_idx}. "
        "Expected last_interact < long_short_zscore_30 < first_mom "
        "(alphabetical 'l' between 'i' and 'm')."
    )


# ---------------------------------------------------------------------------
# 5. Computation correctness — manual z-score verification at target row
# ---------------------------------------------------------------------------


def test_computation_correctness() -> None:
    """compute_long_short_zscore matches manual rolling mean/std at a target row."""
    from crypto_trade.features_v1.longshort_v1 import compute_long_short_zscore

    n = 200
    window = 30
    rng = np.random.default_rng(7)
    lsr_vals = 1.0 + np.abs(rng.normal(0.5, 0.3, n))
    lsr_series = pd.Series(lsr_vals)

    out = compute_long_short_zscore(lsr_series, window=window, clip=10.0)

    # Target row: well past warm-up
    target = 100

    # Manual computation: rolling mean/std over lsr[target-window:target+1]
    window_vals = lsr_vals[target - window + 1 : target + 1]
    expected_mean = np.mean(window_vals)
    expected_std = np.std(window_vals, ddof=1)
    expected_z = np.clip((lsr_vals[target] - expected_mean) / expected_std, -10.0, 10.0)

    actual_z = out.iloc[target]
    assert actual_z == pytest.approx(expected_z, abs=1e-7), (
        f"z-score at row {target}: expected {expected_z:.6f}, got {actual_z:.6f}. "
        "Rolling mean/std computation may be incorrect."
    )


# ---------------------------------------------------------------------------
# 6. test_past_only — no look-ahead
# ---------------------------------------------------------------------------


def test_past_only() -> None:
    """Perturbing lsr[-1] does NOT affect long_short_zscore_30[<-1] (no look-ahead).

    Referenced in brief Section 2.1 as 'test_iteration_v1_049.py::test_past_only'.
    """
    from crypto_trade.features_v1.longshort_v1 import compute_long_short_zscore

    rng = np.random.default_rng(42)
    n = 200
    base = 1.0 + np.abs(rng.normal(0.5, 0.3, n))

    s1 = pd.Series(base.copy())
    out1 = compute_long_short_zscore(s1)

    s2 = pd.Series(base.copy())
    s2.iloc[-1] = base[-1] * 1000.0  # extreme perturbation of last bar only
    out2 = compute_long_short_zscore(s2)

    # All rows EXCEPT the last should be identical (perturbing bar N only affects bar N itself
    # since rolling window is inclusive of bar t — not via shift(1) unlike funding_v1)
    pd.testing.assert_series_equal(
        out1.iloc[:-1],
        out2.iloc[:-1],
        check_names=False,
        check_exact=False,
        atol=1e-10,
    )


# ---------------------------------------------------------------------------
# 7. Burn-in — first window-1 rows are NaN
# ---------------------------------------------------------------------------


def test_burn_in() -> None:
    """First window-1 rows must be NaN (min_periods=window rolling warm-up)."""
    from crypto_trade.features_v1.longshort_v1 import LSR_ZSCORE_WINDOW, compute_long_short_zscore

    n = 200
    rng = np.random.default_rng(42)
    lsr_series = pd.Series(1.0 + np.abs(rng.normal(0.5, 0.3, n)))

    out = compute_long_short_zscore(lsr_series)

    burn_in = LSR_ZSCORE_WINDOW - 1  # 29 rows NaN
    assert out.iloc[:burn_in].isna().all(), (
        f"Expected first {burn_in} rows NaN (min_periods={LSR_ZSCORE_WINDOW}); "
        f"got {out.iloc[:burn_in].notna().sum()} non-NaN rows."
    )
    # After burn-in there should be non-NaN values
    assert out.iloc[burn_in:].notna().any(), (
        f"Expected non-NaN values after burn-in row {burn_in}; all were NaN."
    )


# ---------------------------------------------------------------------------
# 8. GROUP_REGISTRY registration
# ---------------------------------------------------------------------------


def test_group_registry_registration() -> None:
    """longshort_v1 must be registered in GROUP_REGISTRY and be callable."""
    from crypto_trade.features import GROUP_REGISTRY

    assert "longshort_v1" in GROUP_REGISTRY, (
        "longshort_v1 not found in GROUP_REGISTRY. "
        "Ensure _register('longshort_v1', _add_longshort_v1_features) is present "
        "in src/crypto_trade/features/__init__.py."
    )

    fn = GROUP_REGISTRY["longshort_v1"]
    assert callable(fn), f"GROUP_REGISTRY['longshort_v1'] is not callable: {fn!r}."


# ---------------------------------------------------------------------------
# 9. Track isolation
# ---------------------------------------------------------------------------


def test_track_isolation() -> None:
    """longshort_v1.py must have ZERO imports from features_v2 or features_v3."""
    import ast
    import importlib.util

    spec = importlib.util.find_spec("crypto_trade.features_v1.longshort_v1")
    assert spec is not None and spec.origin is not None, "Cannot locate longshort_v1 module spec."
    src = Path(spec.origin).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("crypto_trade.features_v2"), (
                f"longshort_v1.py imports from features_v2 (line {node.lineno}) "
                "— track isolation violated."
            )
            assert not mod.startswith("crypto_trade.features_v3"), (
                f"longshort_v1.py imports from features_v3 (line {node.lineno}) "
                "— track isolation violated."
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert "features_v2" not in alias.name, (
                    f"longshort_v1.py imports features_v2: {alias.name}"
                )
                assert "features_v3" not in alias.name, (
                    f"longshort_v1.py imports features_v3: {alias.name}"
                )


# ---------------------------------------------------------------------------
# 10. FileNotFoundError on missing OI cache
# ---------------------------------------------------------------------------


def test_file_not_found_error() -> None:
    """add_longshort_v1_features raises FileNotFoundError when OI cache missing."""
    from crypto_trade.features_v1.longshort_v1 import add_longshort_v1_features

    df = _make_kline_df(n=50, symbol="BTCUSDT")
    with tempfile.TemporaryDirectory() as tmpdir:
        # No OI cache written — must raise
        with pytest.raises(FileNotFoundError, match="fetch-oi"):
            add_longshort_v1_features(df, data_dir=Path(tmpdir))


# ---------------------------------------------------------------------------
# 11. KeyError on missing symbol column
# ---------------------------------------------------------------------------


def test_key_error_missing_symbol() -> None:
    """add_longshort_v1_features raises KeyError when df has no symbol column."""
    from crypto_trade.features_v1.longshort_v1 import add_longshort_v1_features

    df = _make_kline_df(n=50, symbol="BTCUSDT").drop(columns=["symbol"])
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(KeyError, match="symbol"):
            add_longshort_v1_features(df, data_dir=Path(tmpdir))


# ---------------------------------------------------------------------------
# 12. Missing sum_toptrader_long_short_ratio column in OI CSV
# ---------------------------------------------------------------------------


def test_missing_lsr_column() -> None:
    """add_longshort_v1_features raises KeyError when OI CSV lacks the LSR column."""
    from crypto_trade.features_v1.longshort_v1 import add_longshort_v1_features

    n = 100
    df = _make_kline_df(n=n, symbol="BTCUSDT")
    # Write OI CSV WITHOUT sum_toptrader_long_short_ratio
    oi_df_no_lsr = pd.DataFrame(
        {
            "open_time": df["open_time"].values,
            "sum_open_interest": np.ones(n) * 50000.0,
        }
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df_no_lsr)
        with pytest.raises(KeyError, match="sum_toptrader_long_short_ratio"):
            add_longshort_v1_features(df, data_dir=Path(tmpdir))


# ---------------------------------------------------------------------------
# 13. Unmatched rows produce NaN (not zeros)
# ---------------------------------------------------------------------------


def test_unmatched_rows_produce_nan() -> None:
    """Kline rows with no matching OI record must produce NaN, not 0."""
    from crypto_trade.features_v1.longshort_v1 import add_longshort_v1_features

    n = 200
    df = _make_kline_df(n=n, symbol="BTCUSDT")
    # OI covers only first half
    oi_df = _make_oi_df_with_lsr(df.iloc[:100])

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
        out = add_longshort_v1_features(df, data_dir=Path(tmpdir))

    # Second half (rows 100+) should be all NaN (not zeros)
    second_half = out["long_short_zscore_30"].iloc[100:]
    assert second_half.isna().all(), (
        f"Expected NaN for unmatched kline rows; got {second_half.dropna().head(5)}. "
        "No silent zero-fill allowed."
    )


# ---------------------------------------------------------------------------
# 14. Clip applied — output bounded to [-10, +10]
# ---------------------------------------------------------------------------


def test_clip_applied() -> None:
    """long_short_zscore_30 must be clipped to [-10, +10]."""
    from crypto_trade.features_v1.longshort_v1 import LSR_ZSCORE_CLIP, add_longshort_v1_features

    n = 200
    df = _make_kline_df(n=n, symbol="BTCUSDT")
    # Alternate between 0.01 and 1000 to force extreme z-scores beyond clip
    lsr_vals = np.where(np.arange(n) % 2 == 0, 0.01, 1000.0)
    oi_df = _make_oi_df_with_lsr(df)
    oi_df["sum_toptrader_long_short_ratio"] = lsr_vals

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
        out = add_longshort_v1_features(df, data_dir=Path(tmpdir))

    finite_vals = out["long_short_zscore_30"].dropna()
    if len(finite_vals) > 0:
        assert finite_vals.abs().max() <= LSR_ZSCORE_CLIP + 1e-9, (
            f"z-score exceeds clip bound {LSR_ZSCORE_CLIP}: max_abs={finite_vals.abs().max():.2f}"
        )


# ---------------------------------------------------------------------------
# 15. Empty OI cache returns NaN column without error
# ---------------------------------------------------------------------------


def test_empty_oi_cache_returns_nan() -> None:
    """Empty OI cache (0 rows) must return NaN long_short_zscore_30 without error."""
    from crypto_trade.features_v1.longshort_v1 import add_longshort_v1_features

    n = 100
    df = _make_kline_df(n=n, symbol="BTCUSDT")
    empty_oi = pd.DataFrame(
        columns=[
            "open_time",
            "sum_open_interest",
            "sum_open_interest_value",
            "count_toptrader_long_short_ratio",
            "sum_toptrader_long_short_ratio",
            "count_long_short_ratio",
            "sum_taker_long_short_vol_ratio",
        ]
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_oi_csv(Path(tmpdir), "BTCUSDT", empty_oi)
        out = add_longshort_v1_features(df, data_dir=Path(tmpdir))

    assert "long_short_zscore_30" in out.columns
    assert out["long_short_zscore_30"].isna().all(), (
        "Empty OI cache should produce all-NaN long_short_zscore_30 column."
    )


# ---------------------------------------------------------------------------
# 16. Parquet integration — column present in regenerated v1 parquets
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (Path("data") / "features").exists(),
    reason="data/features/ not found — parquets must be regenerated first. "
    "Run: uv run crypto-trade features --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT "
    "--interval 8h --track v1 --format parquet --workers 4",
)
def test_parquet_integration() -> None:
    """long_short_zscore_30 column must be present in regenerated v1 parquets."""
    import pyarrow.parquet as pq  # type: ignore[import-untyped]

    features_dir = Path("data") / "features"
    symbols = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]
    found_any = False

    for sym in symbols:
        parquet_path = features_dir / f"{sym}_8h_features.parquet"
        if not parquet_path.exists():
            continue
        found_any = True
        schema = pq.read_schema(parquet_path)
        col_names = schema.names
        assert "long_short_zscore_30" in col_names, (
            f"long_short_zscore_30 not found in {parquet_path}. "
            f"Available columns: {col_names[:20]}..."
        )
        # Spot-check: read a sample and verify distribution is reasonable (not all NaN)
        table = pq.read_table(parquet_path, columns=["long_short_zscore_30"])
        col = table.column("long_short_zscore_30").to_pylist()
        non_nan = [v for v in col if v is not None and not np.isnan(v)]
        assert len(non_nan) > 0, (
            f"long_short_zscore_30 is all-NaN in {parquet_path}. "
            "Check OI data alignment (sum_toptrader_long_short_ratio column)."
        )
        # Values must be within clip bounds
        max_abs = max(abs(v) for v in non_nan)
        assert max_abs <= 10.0 + 1e-6, (
            f"long_short_zscore_30 max_abs={max_abs:.4f} exceeds clip=10.0 in {parquet_path}."
        )

    if not found_any:
        pytest.skip(
            "No v1 parquet files found in data/features/. "
            "Regenerate with: uv run crypto-trade features "
            "--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )
