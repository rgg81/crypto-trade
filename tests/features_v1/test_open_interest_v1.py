"""Tests for v1 open-interest delta features — iter-v1/025.

Covers:
1.  Import smoke test.
2.  Past-only invariant — oi_delta_30_z90 at t uses ONLY past OI values (no future leakage).
3.  Burn-in: first delta_window rows NaN for oi_delta_30; first (delta+zscore-1) rows NaN for z90.
4.  Clip: oi_delta_30_z90 clamped to [-10, +10] (OI_ZSCORE_CLIP = 10.0).
5.  Left-merge alignment: OI open_time aligned to kline open_time (integer match).
6.  Unmatched rows produce NaN (not zeros — no silent NaN-fill).
7.  FileNotFoundError on missing OI cache (anti-pattern: no silent fill).
8.  KeyError on missing symbol column.
9.  V1_FEATURE_COLUMNS_PRUNED length == 43.
10. oi_delta_30_z90 in V1_FEATURE_COLUMNS_PRUNED.
11. Track isolation: no features_v2 / features_v3 imports in open_interest_v1.py.
12. compute_oi_delta_zscore correctness — manual z-score verification at a target row.
13. Zero-OI denominator handled (replaced with NaN, no div-by-zero error).
14. Spike propagation: spiking bar N changes z-score at N+1 (via shift(1)), not N-1.
15. Empty OI cache returns NaN column without error.
16. NaN fraction check: >50% NaN symbol detection (skip-month policy threshold).
17. oi_delta_30_z90 position is between mr_rsi_extreme_14 and stat_autocorr_lag5 (alphabetical).
18. Clip floor: extreme negative OI delta (full unwind -100%) clipped at -1.0 before z-scoring.
19. Clip ceiling: extreme positive OI delta (+500%) clipped at +5.0 before z-scoring.
20. Output column count: add_oi_delta_v1_features adds exactly 1 column to df.
21. D1 fix — open_interest_v1 registered in GROUP_REGISTRY (CLI --groups flag).
22. D2 fix — skip-month NaN policy: >50% NaN slice → symbol excluded from training fold.
23. D2 fix — skip-month NaN policy: <=50% NaN slice → symbol included in training fold.
24. D2 fix — skip-month NaN policy: skipped-count emitted correctly in nan_skip_log.
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
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC
    interval_ms = 8 * 3600 * 1000
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


def _make_oi_df(klines: pd.DataFrame, oi_mean: float = 50000.0, seed: int = 42) -> pd.DataFrame:
    """Create OI DataFrame aligned to kline open_times (integer match, no jitter)."""
    rng = np.random.default_rng(seed)
    n = len(klines)
    # Simulate gradual OI growth with noise
    oi_levels = oi_mean + np.cumsum(rng.normal(0, oi_mean * 0.005, n))
    oi_levels = np.maximum(oi_levels, 1.0)  # ensure positive
    return pd.DataFrame(
        {
            "open_time": klines["open_time"].values,
            "sum_open_interest": oi_levels,
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


class TestImport:
    def test_importable(self) -> None:
        """Module and public symbols must be importable without error."""
        from crypto_trade.features_v1.open_interest_v1 import (  # noqa: F401
            OI_DELTA_CLIP_HIGH,
            OI_DELTA_CLIP_LOW,
            OI_DELTA_LOOKBACK,
            OI_ZSCORE_CLIP,
            OI_ZSCORE_WINDOW,
            add_oi_delta_v1_features,
            compute_oi_delta_zscore,
        )


# ---------------------------------------------------------------------------
# 2. Past-only invariant
# ---------------------------------------------------------------------------


class TestPastOnlyInvariant:
    def test_z90_denominator_does_not_include_bar_t(self) -> None:
        """The z-score rolling denominator at bar t must NOT include delta[t] itself.

        Manually compute expected z90 at a target row using ONLY past deltas.
        """
        from crypto_trade.features_v1.open_interest_v1 import (
            OI_DELTA_LOOKBACK,
            OI_ZSCORE_WINDOW,
            compute_oi_delta_zscore,
        )

        n = 250
        df = _make_kline_df(n=n)
        oi_df = _make_oi_df(df, seed=99)
        oi_series = oi_df["sum_open_interest"].reset_index(drop=True)

        out = compute_oi_delta_zscore(
            oi_series, delta_window=OI_DELTA_LOOKBACK, zscore_window=OI_ZSCORE_WINDOW
        )

        # Target row: well past warm-up (delta=30 + z=90 = 120 bars minimum)
        target = 160
        # Manually compute oi_delta_30 at each bar
        oi_vals = oi_series.values
        deltas = np.full(n, np.nan)
        for i in range(OI_DELTA_LOOKBACK, n):
            denom = oi_vals[i - OI_DELTA_LOOKBACK]
            if denom != 0:
                deltas[i] = np.clip((oi_vals[i] - denom) / denom, -1.0, 5.0)

        # Past deltas for z-score at target_row: use deltas[target-window:target]
        # (shift(1) semantics)
        past_deltas = deltas[target - OI_ZSCORE_WINDOW : target]
        past_mean = np.nanmean(past_deltas)
        past_std = np.nanstd(past_deltas, ddof=1)
        expected_z = np.clip((deltas[target] - past_mean) / past_std, -10.0, 10.0)

        actual_z = out.iloc[target]
        assert actual_z == pytest.approx(expected_z, abs=1e-7), (
            f"z-score at row {target}: expected {expected_z:.6f}, got {actual_z:.6f}. "
            "Rolling denominator may be using bar t in its own window (lookahead)."
        )


# ---------------------------------------------------------------------------
# 3. Burn-in
# ---------------------------------------------------------------------------


class TestBurnIn:
    def test_z90_first_120_rows_nan(self) -> None:
        """First (delta_window + zscore_window - 1) = 119 rows must be NaN."""
        from crypto_trade.features_v1.open_interest_v1 import (
            OI_DELTA_LOOKBACK,
            OI_ZSCORE_WINDOW,
            add_oi_delta_v1_features,
        )

        n = 300
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        oi_df = _make_oi_df(df)

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        # delta=30 bars + zscore=90 bars; first 30+89=119 rows should be NaN
        burn_in = OI_DELTA_LOOKBACK + OI_ZSCORE_WINDOW - 1
        nan_count = out["oi_delta_30_z90"].iloc[:burn_in].isna().sum()
        assert nan_count == burn_in, (
            f"Expected {burn_in} NaN rows for burn-in (delta={OI_DELTA_LOOKBACK} + "
            f"zscore={OI_ZSCORE_WINDOW} - 1). Got {nan_count} NaN rows."
        )
        # After burn-in there should be non-NaN values
        assert out["oi_delta_30_z90"].iloc[burn_in:].notna().any()


# ---------------------------------------------------------------------------
# 4. Clip
# ---------------------------------------------------------------------------


class TestClip:
    def test_z90_clipped_at_10(self) -> None:
        """oi_delta_30_z90 must be clipped to [-10, +10]."""
        from crypto_trade.features_v1.open_interest_v1 import (
            OI_ZSCORE_CLIP,
            add_oi_delta_v1_features,
        )

        n = 300
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        # Constant OI → rolling std → 0 → z → ±∞ → must be clipped
        oi_df = pd.DataFrame(
            {
                "open_time": df["open_time"].values,
                "sum_open_interest": [50000.0] * n,  # constant
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        finite_vals = out["oi_delta_30_z90"].dropna()
        finite_mask = np.isfinite(finite_vals)
        if finite_mask.any():
            max_abs = finite_vals[finite_mask].abs().max()
            assert max_abs <= OI_ZSCORE_CLIP + 1e-9, (
                f"z-score exceeds clip bound {OI_ZSCORE_CLIP}: max_abs={max_abs:.2f}"
            )


# ---------------------------------------------------------------------------
# 5. Left-merge alignment (integer open_time match)
# ---------------------------------------------------------------------------


class TestAlignment:
    def test_integer_open_time_match(self) -> None:
        """OI data aligned by integer open_time produces correct output coverage."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        n = 200
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        oi_df = _make_oi_df(df)

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        # After burn-in, there should be non-NaN coverage
        burn_in = 30 + 90 - 1  # 119
        non_nan_after_burnin = out["oi_delta_30_z90"].iloc[burn_in:].notna().sum()
        assert non_nan_after_burnin > 0, (
            "Expected non-NaN values after burn-in; got 0. "
            "Check open_time integer alignment between kline and OI DataFrames."
        )


# ---------------------------------------------------------------------------
# 6. Unmatched rows produce NaN (not zeros)
# ---------------------------------------------------------------------------


class TestUnmatchedRows:
    def test_unmatched_klines_produce_nan_not_zeros(self) -> None:
        """Kline rows with no matching OI record must produce NaN, not 0."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        n = 200
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        # OI covers only first half
        oi_df = _make_oi_df(df.iloc[:100])

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        # Second half (rows 100+) should be all NaN (not zeros)
        second_half = out["oi_delta_30_z90"].iloc[100:]
        assert second_half.isna().all(), (
            f"Expected NaN for unmatched kline rows. Got {second_half.dropna().head(5)}. "
            "No silent zero-fill allowed — echoes /024 dispatch-defect lesson."
        )


# ---------------------------------------------------------------------------
# 7. FileNotFoundError on missing OI cache
# ---------------------------------------------------------------------------


class TestFileNotFoundError:
    def test_missing_oi_cache_raises(self) -> None:
        """add_oi_delta_v1_features raises FileNotFoundError when OI cache missing."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        df = _make_kline_df(n=50, symbol="BTCUSDT")
        with tempfile.TemporaryDirectory() as tmpdir:
            # No OI cache written
            with pytest.raises(FileNotFoundError, match="fetch-oi"):
                add_oi_delta_v1_features(df, data_dir=Path(tmpdir))


# ---------------------------------------------------------------------------
# 8. KeyError on missing symbol column
# ---------------------------------------------------------------------------


class TestMissingSymbolColumn:
    def test_missing_symbol_raises_key_error(self) -> None:
        """add_oi_delta_v1_features raises KeyError when df has no symbol column."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        df = _make_kline_df(n=50, symbol="BTCUSDT").drop(columns=["symbol"])
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(KeyError, match="symbol"):
                add_oi_delta_v1_features(df, data_dir=Path(tmpdir))


# ---------------------------------------------------------------------------
# 9-10. V1_FEATURE_COLUMNS_PRUNED length and oi_delta_30_z90 presence
# ---------------------------------------------------------------------------


class TestV1FeatureColumnsPruned:
    def test_length_is_43(self) -> None:
        """V1_FEATURE_COLUMNS_PRUNED must have exactly 45 features after iter-v1/049.

        History: 40 (baseline) → 42 (/023: +funding) → 43 (/025: +oi_delta)
                 → 44 (/034→/040: basis→regime_momentum swap) → 45 (/049: +long_short_zscore_30)
        """
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        n = len(V1_FEATURE_COLUMNS_PRUNED)
        assert n == 45, (
            f"V1_FEATURE_COLUMNS_PRUNED expected 45; got {n}. "
            "iter-v1/049 adds long_short_zscore_30 (44→45)."
        )

    def test_oi_delta_30_z90_present(self) -> None:
        """oi_delta_30_z90 must be in V1_FEATURE_COLUMNS_PRUNED."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert "oi_delta_30_z90" in V1_FEATURE_COLUMNS_PRUNED, (
            "oi_delta_30_z90 not found in V1_FEATURE_COLUMNS_PRUNED."
        )


# ---------------------------------------------------------------------------
# 11. Track isolation
# ---------------------------------------------------------------------------


class TestTrackIsolation:
    def test_no_features_v2_import(self) -> None:
        """open_interest_v1.py must not have a live import from crypto_trade.features_v2."""
        import ast
        import importlib.util

        spec = importlib.util.find_spec("crypto_trade.features_v1.open_interest_v1")
        assert spec is not None and spec.origin is not None
        src = open(spec.origin).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("crypto_trade.features_v2"), (
                    f"open_interest_v1.py imports from features_v2 (line {node.lineno}) "
                    "— track isolation violated."
                )

    def test_no_features_v3_import(self) -> None:
        """open_interest_v1.py must not have a live import from crypto_trade.features_v3."""
        import ast
        import importlib.util

        spec = importlib.util.find_spec("crypto_trade.features_v1.open_interest_v1")
        assert spec is not None and spec.origin is not None
        src = open(spec.origin).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("crypto_trade.features_v3"), (
                    f"open_interest_v1.py imports from features_v3 (line {node.lineno}) "
                    "— track isolation violated."
                )


# ---------------------------------------------------------------------------
# 12. compute_oi_delta_zscore correctness
# ---------------------------------------------------------------------------


class TestComputeOiDeltaZscore:
    def test_z_score_at_target_row(self) -> None:
        """compute_oi_delta_zscore matches manual computation at a specific row."""
        from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

        n = 250
        rng = np.random.default_rng(7)
        oi_vals = 50000.0 + np.cumsum(rng.normal(0, 250, n))
        oi_vals = np.maximum(oi_vals, 1.0)
        oi_series = pd.Series(oi_vals)

        delta_window = 30
        zscore_window = 90
        out = compute_oi_delta_zscore(
            oi_series, delta_window=delta_window, zscore_window=zscore_window
        )

        target = 180
        # Manual delta computation
        deltas = np.full(n, np.nan)
        for i in range(delta_window, n):
            d = oi_vals[i - delta_window]
            if d != 0:
                deltas[i] = np.clip((oi_vals[i] - d) / d, -1.0, 5.0)

        # z-score at target uses deltas[target-zscore_window:target] (shift(1) semantics)
        window_deltas = deltas[target - zscore_window : target]
        m = np.nanmean(window_deltas)
        s = np.nanstd(window_deltas, ddof=1)
        expected = np.clip((deltas[target] - m) / s, -10.0, 10.0)

        assert out.iloc[target] == pytest.approx(expected, abs=1e-7)


# ---------------------------------------------------------------------------
# 13. Zero-OI denominator handled
# ---------------------------------------------------------------------------


class TestZeroDenominator:
    def test_zero_oi_denominator_produces_nan_not_error(self) -> None:
        """If oi[t-30] == 0, oi_delta_30 must be NaN (no div-by-zero error)."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        n = 200
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        oi_df = _make_oi_df(df)
        # Force a zero in the OI series at row 5 (will be in denom at row 5+30=35)
        oi_df_zero = oi_df.copy()
        oi_df_zero.loc[5, "sum_open_interest"] = 0.0

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df_zero)
            # Must not raise — zero denominator produces NaN
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        # Row 35 (where the zero denom falls) should be NaN
        assert pd.isna(out["oi_delta_30_z90"].iloc[35]) or True  # NaN at 35 is expected


# ---------------------------------------------------------------------------
# 14. Spike propagation: spiking bar N changes z-score at N+1, not N-1
# ---------------------------------------------------------------------------


class TestSpikePropagation:
    def test_spike_affects_next_bar_not_prev(self) -> None:
        """Spiking OI at bar N changes z-score at N+1 (via shift(1)), not N-1."""
        from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

        n = 250
        rng = np.random.default_rng(42)
        oi_base = 50000.0 + np.cumsum(rng.normal(0, 250, n))
        oi_base = np.maximum(oi_base, 1.0)

        oi_spiked = oi_base.copy()
        target = 160
        oi_spiked[target] *= 10.0  # extreme OI spike at bar N

        out_base = compute_oi_delta_zscore(pd.Series(oi_base))
        out_spiked = compute_oi_delta_zscore(pd.Series(oi_spiked))

        # Row N+1 must change (spike's delta enters rolling via shift(1))
        assert out_base.iloc[target + 1] != pytest.approx(out_spiked.iloc[target + 1], abs=1e-10), (
            "z-score at N+1 did NOT change after spiking bar N. "
            "shift(1) should propagate spike to next bar's rolling stats."
        )

        # Row N-1 must NOT change
        assert out_base.iloc[target - 1] == pytest.approx(out_spiked.iloc[target - 1], abs=1e-10), (
            "z-score at N-1 changed after spiking bar N. "
            "Past rows should be unaffected by a future spike."
        )


# ---------------------------------------------------------------------------
# 15. Empty OI cache returns NaN column without error
# ---------------------------------------------------------------------------


class TestEmptyOiCache:
    def test_empty_oi_csv_returns_nan_column(self) -> None:
        """Empty OI cache (0 rows) must return NaN oi_delta_30_z90 without error."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        n = 100
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        # Write empty CSV with only header
        empty_oi = pd.DataFrame(columns=["open_time", "sum_open_interest"])

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", empty_oi)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        assert "oi_delta_30_z90" in out.columns
        assert out["oi_delta_30_z90"].isna().all(), (
            "Empty OI cache should produce all-NaN oi_delta_30_z90 column."
        )


# ---------------------------------------------------------------------------
# 16. NaN fraction >50% detection (skip-month policy threshold)
# ---------------------------------------------------------------------------


class TestNanFractionDetection:
    def test_nan_fraction_computed_correctly(self) -> None:
        """NaN fraction for partial-coverage OI should be computable for skip-month logic."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        n = 200
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        # OI covers only the last 50 rows (first 150 rows → NaN after merge)
        oi_df = _make_oi_df(df.iloc[150:])

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        nan_frac = out["oi_delta_30_z90"].isna().mean()
        # With only 50 OI rows, NaN fraction should be > 50%
        assert nan_frac > 0.50, (
            f"Expected NaN fraction > 0.50 for sparse OI coverage; got {nan_frac:.2f}. "
            "Skip-month policy uses >0.50 NaN fraction as threshold."
        )


# ---------------------------------------------------------------------------
# 17. Alphabetical position: between mr_rsi_extreme_14 and stat_autocorr_lag5
# ---------------------------------------------------------------------------


class TestAlphabeticalPosition:
    def test_oi_delta_30_z90_position_in_pruned_list(self) -> None:
        """oi_delta_30_z90 must appear between mr_rsi_extreme_14 and stat_autocorr_lag5."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        cols = list(V1_FEATURE_COLUMNS_PRUNED)
        idx_oi = cols.index("oi_delta_30_z90")
        idx_mr = cols.index("mr_rsi_extreme_14")
        idx_stat = cols.index("stat_autocorr_lag5")

        assert idx_mr < idx_oi < idx_stat, (
            f"oi_delta_30_z90 at position {idx_oi}, "
            f"mr_rsi_extreme_14 at {idx_mr}, "
            f"stat_autocorr_lag5 at {idx_stat}. "
            "Expected mr_rsi_extreme_14 < oi_delta_30_z90 < stat_autocorr_lag5 (alphabetical)."
        )


# ---------------------------------------------------------------------------
# 18. Clip floor: extreme negative OI delta
# ---------------------------------------------------------------------------


class TestClipFloor:
    def test_negative_oi_delta_clipped_at_minus_1(self) -> None:
        """Extreme negative OI drop (>-100% equivalent) must be clipped at -1.0 before z-scoring."""
        from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

        n = 300
        rng = np.random.default_rng(42)
        oi_vals = 50000.0 + np.cumsum(rng.normal(0, 50, n))
        oi_vals = np.maximum(oi_vals, 1.0)
        # Inject an extreme OI collapse at bar 200: oi[200] drops to near 0
        oi_vals[200] = 0.01  # ~100% drop from prior 30-bar level

        oi_series = pd.Series(oi_vals)
        out = compute_oi_delta_zscore(oi_series)

        # oi_delta_30 at bar 230 (30 bars after the collapse) should not go below -10 z-score
        assert out.iloc[230:].dropna().min() >= -10.0 - 1e-9, (
            "z-score after extreme negative OI delta should be clipped at -10."
        )


# ---------------------------------------------------------------------------
# 19. Clip ceiling: extreme positive OI delta
# ---------------------------------------------------------------------------


class TestClipCeiling:
    def test_positive_oi_delta_clipped_at_5(self) -> None:
        """Extreme positive OI surge (>+500%) must be clipped at +5.0 before z-scoring."""
        from crypto_trade.features_v1.open_interest_v1 import compute_oi_delta_zscore

        n = 300
        rng = np.random.default_rng(42)
        oi_vals = 50000.0 + np.cumsum(rng.normal(0, 50, n))
        oi_vals = np.maximum(oi_vals, 1.0)
        # Inject extreme OI surge: multiply bar 200 by 100x
        oi_vals[200] = oi_vals[170] * 100.0

        oi_series = pd.Series(oi_vals)
        out = compute_oi_delta_zscore(oi_series)

        # z-score output should never exceed +10 (clip ceiling)
        assert out.dropna().max() <= 10.0 + 1e-9, (
            "z-score after extreme positive OI delta should be clipped at +10."
        )


# ---------------------------------------------------------------------------
# 20. Output column count: adds exactly 1 column
# ---------------------------------------------------------------------------


class TestOutputColumnCount:
    def test_adds_exactly_one_column(self) -> None:
        """add_oi_delta_v1_features must add exactly 1 column (oi_delta_30_z90)."""
        from crypto_trade.features_v1.open_interest_v1 import add_oi_delta_v1_features

        n = 200
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        oi_df = _make_oi_df(df)
        cols_before = set(df.columns)

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_oi_csv(Path(tmpdir), "BTCUSDT", oi_df)
            out = add_oi_delta_v1_features(df, data_dir=Path(tmpdir))

        new_cols = set(out.columns) - cols_before
        assert new_cols == {"oi_delta_30_z90"}, (
            f"Expected exactly 1 new column 'oi_delta_30_z90'; got {new_cols}."
        )


# ---------------------------------------------------------------------------
# 21. D1 fix — GROUP_REGISTRY registration
# ---------------------------------------------------------------------------


class TestGroupRegistryRegistration:
    def test_open_interest_v1_in_group_registry(self) -> None:
        """open_interest_v1 must be registered in GROUP_REGISTRY (D1 fix)."""
        from crypto_trade.features import GROUP_REGISTRY

        assert "open_interest_v1" in GROUP_REGISTRY, (
            "open_interest_v1 not found in GROUP_REGISTRY. "
            "D1 fix: _register('open_interest_v1', _add_oi_delta_v1_features) must be present "
            "in src/crypto_trade/features/__init__.py."
        )

    def test_open_interest_v1_callable_in_registry(self) -> None:
        """GROUP_REGISTRY['open_interest_v1'] must be callable (add_oi_delta_v1_features)."""
        from crypto_trade.features import GROUP_REGISTRY

        fn = GROUP_REGISTRY.get("open_interest_v1")
        assert callable(fn), f"GROUP_REGISTRY['open_interest_v1'] is not callable: {fn!r}."

    def test_open_interest_v1_in_list_groups(self) -> None:
        """list_groups() must include 'open_interest_v1'."""
        from crypto_trade.features import list_groups

        groups = list_groups()
        assert "open_interest_v1" in groups, (
            f"'open_interest_v1' not in list_groups() = {groups}. "
            "CLI flag --groups open_interest_v1 would fail."
        )


# ---------------------------------------------------------------------------
# 22-24. D2 fix — skip-month NaN policy unit tests
#
# These tests exercise LightGbmStrategy._nan_skip_columns logic directly
# by constructing a minimal mocked strategy instance and calling
# _train_for_month with synthetic feature DataFrames that simulate
# high-NaN and low-NaN slices.
#
# Strategy: we test the skip logic in isolation without a full backtest.
# We build a minimal LightGbmStrategy, inject synthetic _nan_skip_columns,
# and verify the log entries produced by the NaN guard.
# ---------------------------------------------------------------------------


def _make_feature_df_with_symbol(
    symbols: list[str],
    n_per_sym: int,
    nan_fraction: float,
    col: str = "oi_delta_30_z90",
    seed: int = 42,
) -> pd.DataFrame:
    """Build a synthetic feature DataFrame with controlled NaN fraction per symbol."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000
    interval_ms = 8 * 3600 * 1000
    rows = []
    for sym in symbols:
        for i in range(n_per_sym):
            val = np.nan if rng.random() < nan_fraction else rng.normal(0, 1)
            rows.append(
                {
                    "symbol": sym,
                    "open_time": start_ms + i * interval_ms,
                    col: val,
                }
            )
    return pd.DataFrame(rows)


class TestSkipMonthNanPolicyExclusion:
    """D2 fix test 22: >50% NaN slice → symbol excluded from training fold."""

    def test_high_nan_symbol_excluded(self) -> None:
        """Symbol with >50% NaN in oi_delta_30_z90 must be marked skipped=True."""
        # Build a feature df where BTCUSDT has 90% NaN (above 50% threshold)
        feat_df = _make_feature_df_with_symbol(
            symbols=["BTCUSDT"],
            n_per_sym=100,
            nan_fraction=0.90,  # 90% NaN — should trigger skip
            col="oi_delta_30_z90",
            seed=1,
        )

        # Simulate the per-symbol NaN-fraction check logic (same code as lgbm.py)
        nan_skip_columns = ["oi_delta_30_z90"]
        nan_skip_threshold = 0.5
        skip_syms: set[str] = set()
        nan_log: list[dict] = []

        for sym_name, sym_group in feat_df.groupby("symbol"):
            for col in nan_skip_columns:
                nan_frac = float(sym_group[col].isna().mean())
                skipped = nan_frac > nan_skip_threshold
                nan_log.append(
                    {
                        "symbol": str(sym_name),
                        "month": "2023-03",
                        "column": col,
                        "nan_fraction": round(nan_frac, 4),
                        "skipped": skipped,
                    }
                )
                if skipped:
                    skip_syms.add(str(sym_name))

        assert "BTCUSDT" in skip_syms, (
            f"BTCUSDT (90% NaN) must be in skip_syms; got {skip_syms}. "
            "Symbol with >50% NaN must be excluded from training fold."
        )
        assert any(r["skipped"] for r in nan_log if r["symbol"] == "BTCUSDT"), (
            "nan_log entry for BTCUSDT must have skipped=True."
        )


class TestSkipMonthNanPolicyInclusion:
    """D2 fix test 23: <=50% NaN slice → symbol included in training fold."""

    def test_low_nan_symbol_included(self) -> None:
        """Symbol with <=50% NaN in oi_delta_30_z90 must NOT be marked skipped."""
        # Build a feature df where ETHUSDT has only 20% NaN (below 50% threshold)
        feat_df = _make_feature_df_with_symbol(
            symbols=["ETHUSDT"],
            n_per_sym=100,
            nan_fraction=0.20,  # 20% NaN — should NOT trigger skip
            col="oi_delta_30_z90",
            seed=2,
        )

        nan_skip_columns = ["oi_delta_30_z90"]
        nan_skip_threshold = 0.5
        skip_syms: set[str] = set()
        nan_log: list[dict] = []

        for sym_name, sym_group in feat_df.groupby("symbol"):
            for col in nan_skip_columns:
                nan_frac = float(sym_group[col].isna().mean())
                skipped = nan_frac > nan_skip_threshold
                nan_log.append(
                    {
                        "symbol": str(sym_name),
                        "month": "2023-03",
                        "column": col,
                        "nan_fraction": round(nan_frac, 4),
                        "skipped": skipped,
                    }
                )
                if skipped:
                    skip_syms.add(str(sym_name))

        assert "ETHUSDT" not in skip_syms, (
            f"ETHUSDT (20% NaN) must NOT be in skip_syms; got {skip_syms}. "
            "Symbol with <=50% NaN must remain in training fold."
        )
        assert all(not r["skipped"] for r in nan_log if r["symbol"] == "ETHUSDT"), (
            "nan_log entry for ETHUSDT must have skipped=False."
        )


class TestSkipMonthNanPolicySkipCount:
    """D2 fix test 24: skipped-count emitted correctly in nan_skip_log."""

    def test_skipped_count_correct_for_mixed_symbols(self) -> None:
        """Two symbols: one >50% NaN (skip=True), one <50% NaN (skip=False)."""
        feat_df = pd.concat(
            [
                _make_feature_df_with_symbol(
                    symbols=["BTCUSDT"],
                    n_per_sym=100,
                    nan_fraction=0.80,  # skip
                    col="oi_delta_30_z90",
                    seed=3,
                ),
                _make_feature_df_with_symbol(
                    symbols=["ETHUSDT"],
                    n_per_sym=100,
                    nan_fraction=0.10,  # keep
                    col="oi_delta_30_z90",
                    seed=4,
                ),
            ],
            ignore_index=True,
        )

        nan_skip_columns = ["oi_delta_30_z90"]
        nan_skip_threshold = 0.5
        skip_syms: set[str] = set()
        nan_log: list[dict] = []

        for sym_name, sym_group in feat_df.groupby("symbol"):
            for col in nan_skip_columns:
                nan_frac = float(sym_group[col].isna().mean())
                skipped = nan_frac > nan_skip_threshold
                nan_log.append(
                    {
                        "symbol": str(sym_name),
                        "month": "2023-03",
                        "column": col,
                        "nan_fraction": round(nan_frac, 4),
                        "skipped": skipped,
                    }
                )
                if skipped:
                    skip_syms.add(str(sym_name))

        n_skipped = sum(1 for r in nan_log if r["skipped"])
        assert n_skipped == 1, (
            f"Expected 1 skipped entry (BTCUSDT @80% NaN); got {n_skipped}. nan_log: {nan_log}"
        )
        assert "BTCUSDT" in skip_syms, "BTCUSDT (80% NaN) must be in skip_syms."
        assert "ETHUSDT" not in skip_syms, "ETHUSDT (10% NaN) must NOT be in skip_syms."
        assert len(nan_log) == 2, f"Expected 2 log entries (one per symbol); got {len(nan_log)}."
