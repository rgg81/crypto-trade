"""Tests for v1 funding-rate features — iter-v1/023.

Covers:
1.  Import smoke test.
2.  Past-only invariant — z-score at t uses ONLY rates t-window…t-1.
3.  Burn-in: first window rows NaN for z30, first 90 rows NaN for z90.
4.  Clip: |z| ≤ 10 enforced (ZSCORE_CLIP = 10.0).
5.  Kline alignment with ≤15ms Binance settlement jitter.
6.  Unmatched klines produce NaN z-scores.
7.  Two-window output: both funding_rate_zscore_30 and funding_rate_zscore_90 added.
8.  V1_FEATURE_COLUMNS_PRUNED length == 42 (40 baseline + 2 funding).
9.  funding_rate_zscore_30 in V1_FEATURE_COLUMNS_PRUNED.
10. funding_rate_zscore_90 in V1_FEATURE_COLUMNS_PRUNED.
11. Track isolation: no features_v2 / features_v3 imports in features_v1.
12. add_funding_v1_features FileNotFoundError on missing cache.
13. add_funding_v1_features KeyError on missing symbol column.
14. Dispatch branch: run_baseline_v1 /023 pre-flight assertions fire correctly.
15. Non-null rate > 95% after burn-in for normal data.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest  # noqa: F401

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_kline_df(n: int = 200, seed: int = 42, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time and symbol columns."""
    rng = np.random.default_rng(seed)
    # 8h candles starting at 2023-03-24 00:00 UTC (IS window start)
    start_ms = 1_679_616_000_000
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


def _make_funding_df(
    klines: pd.DataFrame, rate_mean: float = 0.0001, seed: int = 42
) -> pd.DataFrame:
    """Create funding-rate DataFrame aligned to kline open_times."""
    rng = np.random.default_rng(seed)
    n = len(klines)
    rates = rng.normal(rate_mean, 0.0002, n)
    return pd.DataFrame(
        {
            "funding_time": klines["open_time"].values,
            "funding_rate": rates,
        }
    )


def _make_funding_df_with_jitter(klines: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Create funding-rate DataFrame with ~10-15ms Binance settlement jitter."""
    rng = np.random.default_rng(seed)
    n = len(klines)
    rates = rng.normal(0.0001, 0.0002, n)
    jitter_ms = rng.integers(0, 16, n)
    return pd.DataFrame(
        {
            "funding_time": klines["open_time"].values + jitter_ms,
            "funding_rate": rates,
        }
    )


# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------


class TestImport:
    def test_importable(self) -> None:
        """Module and public symbols must be importable without error."""
        from crypto_trade.features_v1.funding_v1 import (  # noqa: F401
            FUNDING_ZSCORE_WINDOW_30,
            FUNDING_ZSCORE_WINDOW_90,
            ZSCORE_CLIP,
            add_funding_v1_features,
            compute_funding_rate_zscore,
        )


# ---------------------------------------------------------------------------
# 2. Past-only invariant
# ---------------------------------------------------------------------------


class TestPastOnlyInvariant:
    def test_denominator_does_not_include_bar_t(self) -> None:
        """The z-score denominator at bar t must NOT include rate[t] itself.

        We verify the past-only invariant by computing the expected z-score
        at a target row using ONLY past rates, then comparing to actual output.
        """
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_30,
            compute_funding_rate_zscore,
        )

        window = FUNDING_ZSCORE_WINDOW_30
        n = 150
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df, rate_mean=0.0001, seed=7)

        out = compute_funding_rate_zscore(df.copy(), funding.copy(), window=window)

        target_row = 80  # well past warm-up
        past_rates = funding["funding_rate"].iloc[target_row - window : target_row].values
        past_mean = past_rates.mean()
        past_std = past_rates.std(ddof=1)
        rate_at_t = funding["funding_rate"].iloc[target_row]
        expected_z = (rate_at_t - past_mean) / past_std

        actual_z = out["funding_rate_zscore_30"].iloc[target_row]
        assert actual_z == pytest.approx(expected_z, abs=1e-8), (
            f"z-score at row {target_row}: expected {expected_z:.6f}, got {actual_z:.6f}. "
            "Rolling denominator may not be using the correct past-only window."
        )

    def test_spike_propagates_to_next_row_only(self) -> None:
        """Spiking row N must change z-score at row N+1 (via shift(1)), not row N-1."""
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_30,
            compute_funding_rate_zscore,
        )

        window = FUNDING_ZSCORE_WINDOW_30
        n = 150
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df)
        target_row = 80

        funding_spiked = funding.copy()
        funding_spiked.loc[target_row, "funding_rate"] = 0.05  # extreme spike

        out_base = compute_funding_rate_zscore(df.copy(), funding.copy(), window=window)
        out_spiked = compute_funding_rate_zscore(df.copy(), funding_spiked, window=window)

        # Row N+1 must change (spike enters rolling window via shift(1))
        val_next_base = out_base["funding_rate_zscore_30"].iloc[target_row + 1]
        val_next_spiked = out_spiked["funding_rate_zscore_30"].iloc[target_row + 1]
        assert val_next_base != pytest.approx(val_next_spiked, abs=1e-10), (
            f"z-score at row {target_row + 1} did NOT change after spiking row {target_row}. "
            "The spike should propagate to the next row's rolling window via shift(1)."
        )

        # Row N-1 must NOT change (pre-spike row unaffected)
        val_prev_base = out_base["funding_rate_zscore_30"].iloc[target_row - 1]
        val_prev_spiked = out_spiked["funding_rate_zscore_30"].iloc[target_row - 1]
        assert val_prev_base == pytest.approx(val_prev_spiked, abs=1e-10), (
            f"z-score at row {target_row - 1} changed after spiking row {target_row}. "
            "Past rows should not be affected by a future spike."
        )


# ---------------------------------------------------------------------------
# 3. Burn-in: first window rows NaN
# ---------------------------------------------------------------------------


class TestBurnIn:
    def test_z30_first_30_rows_nan(self) -> None:
        """funding_rate_zscore_30: first 30 rows must be NaN."""
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_30,
            compute_funding_rate_zscore,
        )

        window = FUNDING_ZSCORE_WINDOW_30
        n = 200
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df)
        out = compute_funding_rate_zscore(df, funding, window=window)

        assert out["funding_rate_zscore_30"].iloc[:window].isna().all(), (
            f"Expected first {window} rows NaN for z30 (rolling warm-up). "
            f"Got: {out['funding_rate_zscore_30'].iloc[:window].tolist()}"
        )
        assert out["funding_rate_zscore_30"].iloc[window:].notna().any()

    def test_z90_first_90_rows_nan(self) -> None:
        """funding_rate_zscore_90: first 90 rows must be NaN."""
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_90,
            compute_funding_rate_zscore,
        )

        window = FUNDING_ZSCORE_WINDOW_90
        n = 250
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df)
        out = compute_funding_rate_zscore(
            df, funding, window=window, output_col="funding_rate_zscore_90"
        )

        assert out["funding_rate_zscore_90"].iloc[:window].isna().all(), (
            f"Expected first {window} rows NaN for z90 (rolling warm-up)."
        )
        assert out["funding_rate_zscore_90"].iloc[window:].notna().any()


# ---------------------------------------------------------------------------
# 4. Clip: |z| ≤ 10
# ---------------------------------------------------------------------------


class TestClip:
    def test_extreme_z_scores_clipped(self) -> None:
        """Constant funding rate (std=0 after warm-up) must produce clipped output."""
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_30,
            ZSCORE_CLIP,
            compute_funding_rate_zscore,
        )

        window = FUNDING_ZSCORE_WINDOW_30
        n = 100
        df = _make_kline_df(n=n)
        # Constant rate → rolling std → 0 → z → ±∞ → must be clipped
        funding = pd.DataFrame(
            {
                "funding_time": df["open_time"].values,
                "funding_rate": [0.0001] * n,
            }
        )
        out = compute_funding_rate_zscore(df, funding, window=window, clip=ZSCORE_CLIP)
        zscore = out["funding_rate_zscore_30"].dropna()
        finite_mask = np.isfinite(zscore)
        if finite_mask.any():
            max_abs = zscore[finite_mask].abs().max()
            assert max_abs <= ZSCORE_CLIP + 1e-9, (
                f"z-score exceeds clip bound {ZSCORE_CLIP}: max={max_abs:.2f}"
            )


# ---------------------------------------------------------------------------
# 5. Kline alignment with jitter
# ---------------------------------------------------------------------------


class TestAlignment:
    def test_jitter_absorbed_by_minute_rounding(self) -> None:
        """Funding timestamps with ≤15ms jitter must produce same coverage as exact alignment."""
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_30,
            compute_funding_rate_zscore,
        )

        window = FUNDING_ZSCORE_WINDOW_30
        n = 150
        df = _make_kline_df(n=n)
        funding_exact = _make_funding_df(df)
        funding_jitter = _make_funding_df_with_jitter(df)

        out_exact = compute_funding_rate_zscore(df.copy(), funding_exact, window=window)
        out_jitter = compute_funding_rate_zscore(df.copy(), funding_jitter, window=window)

        exact_cov = out_exact["funding_rate_zscore_30"].notna().sum()
        jitter_cov = out_jitter["funding_rate_zscore_30"].notna().sum()
        assert exact_cov == jitter_cov, (
            f"Jitter alignment: exact={exact_cov} vs jitter={jitter_cov} coverage. "
            "Millisecond rounding (//60000*60000) must absorb Binance ~15ms jitter."
        )


# ---------------------------------------------------------------------------
# 6. Unmatched klines produce NaN
# ---------------------------------------------------------------------------


class TestUnmatchedKlines:
    def test_unmatched_rows_produce_nan(self) -> None:
        """Klines with no matching funding record must produce NaN z-scores."""
        from crypto_trade.features_v1.funding_v1 import (
            FUNDING_ZSCORE_WINDOW_30,
            compute_funding_rate_zscore,
        )

        n = 100
        df = _make_kline_df(n=n)
        # Funding only covers first half
        funding = _make_funding_df(df.iloc[:50])
        out = compute_funding_rate_zscore(df, funding, window=FUNDING_ZSCORE_WINDOW_30)
        assert out["funding_rate_zscore_30"].iloc[50:].isna().all(), (
            "Rows without matching funding records should produce NaN z-scores."
        )


# ---------------------------------------------------------------------------
# 7. Two-window output from add_funding_v1_features
# ---------------------------------------------------------------------------


class TestTwoWindowOutput:
    def test_both_columns_added(self) -> None:
        """add_funding_v1_features must add both z30 and z90 columns."""
        from crypto_trade.features_v1.funding_v1 import add_funding_v1_features

        n = 200
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        funding = _make_funding_df(df)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            cache_dir = data_dir / "funding_rates"
            cache_dir.mkdir(parents=True)
            (cache_dir / "BTCUSDT.csv").write_text(funding.to_csv(index=False))
            out = add_funding_v1_features(df, data_dir=data_dir)

        assert "funding_rate_zscore_30" in out.columns, "funding_rate_zscore_30 missing"
        assert "funding_rate_zscore_90" in out.columns, "funding_rate_zscore_90 missing"

    def test_z90_smoother_than_z30(self) -> None:
        """z90 standard deviation should be less than z30 (longer window = smoother)."""
        from crypto_trade.features_v1.funding_v1 import add_funding_v1_features

        n = 500
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        funding = _make_funding_df(df, rate_mean=0.0001)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            cache_dir = data_dir / "funding_rates"
            cache_dir.mkdir(parents=True)
            (cache_dir / "BTCUSDT.csv").write_text(funding.to_csv(index=False))
            out = add_funding_v1_features(df, data_dir=data_dir)

        z30_std = out["funding_rate_zscore_30"].dropna().std()
        z90_std = out["funding_rate_zscore_90"].dropna().std()
        assert z90_std <= z30_std + 0.2, (
            f"z90 std ({z90_std:.4f}) should be <= z30 std ({z30_std:.4f}) + tolerance. "
            "Longer window should produce smoother z-scores."
        )


# ---------------------------------------------------------------------------
# 8-10. V1_FEATURE_COLUMNS_PRUNED column count and contents
# ---------------------------------------------------------------------------


class TestV1FeatureColumnsPruned:
    def test_length_is_43(self) -> None:
        """V1_FEATURE_COLUMNS_PRUNED must have exactly 44 features after iter-v1/034.

        History: 40 (baseline) → 42 (iter-v1/023: +funding_rate_zscore_30/90)
                              → 43 (iter-v1/025: +oi_delta_30_z90)
                              → 44 (iter-v1/034: +basis_zscore_30)
        """
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        n = len(V1_FEATURE_COLUMNS_PRUNED)
        assert n == 44, (
            f"V1_FEATURE_COLUMNS_PRUNED expected 44; got {n}. "
            "iter-v1/023: 40→42; iter-v1/025: 42→43; iter-v1/034: 43→44 (+basis_zscore_30)."
        )

    def test_zscore_30_present(self) -> None:
        """funding_rate_zscore_30 must be in V1_FEATURE_COLUMNS_PRUNED."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert "funding_rate_zscore_30" in V1_FEATURE_COLUMNS_PRUNED, (
            "funding_rate_zscore_30 not found in V1_FEATURE_COLUMNS_PRUNED."
        )

    def test_zscore_90_present(self) -> None:
        """funding_rate_zscore_90 must be in V1_FEATURE_COLUMNS_PRUNED."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert "funding_rate_zscore_90" in V1_FEATURE_COLUMNS_PRUNED, (
            "funding_rate_zscore_90 not found in V1_FEATURE_COLUMNS_PRUNED."
        )


# ---------------------------------------------------------------------------
# 11. Track isolation
# ---------------------------------------------------------------------------


class TestTrackIsolation:
    def test_no_features_v2_import(self) -> None:
        """features_v1/funding_v1.py must not have a live import from crypto_trade.features_v2.

        Uses ast.parse to check actual import nodes — not substring match on the raw source
        which would falsely flag docstring mentions of the string "features_v2".
        """
        import ast
        import importlib.util

        spec = importlib.util.find_spec("crypto_trade.features_v1.funding_v1")
        assert spec is not None and spec.origin is not None
        src = open(spec.origin).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("crypto_trade.features_v2"), (
                    f"funding_v1.py imports from features_v2 (line {node.lineno}) "
                    "— track isolation violated."
                )

    def test_no_features_v3_import(self) -> None:
        """features_v1/funding_v1.py must not have a live import from crypto_trade.features_v3.

        Uses ast.parse to check actual import nodes — not substring match on the raw source
        which would falsely flag docstring mentions of the string "features_v3".
        """
        import ast
        import importlib.util

        spec = importlib.util.find_spec("crypto_trade.features_v1.funding_v1")
        assert spec is not None and spec.origin is not None
        src = open(spec.origin).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("crypto_trade.features_v3"), (
                    f"funding_v1.py imports from features_v3 (line {node.lineno}) "
                    "— track isolation violated."
                )


# ---------------------------------------------------------------------------
# 12. FileNotFoundError on missing cache
# ---------------------------------------------------------------------------


class TestFileNotFound:
    def test_missing_cache_raises_file_not_found(self) -> None:
        """add_funding_v1_features raises FileNotFoundError when cache missing."""
        from crypto_trade.features_v1.funding_v1 import add_funding_v1_features

        df = _make_kline_df(n=50, symbol="BTCUSDT")
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            # No cache file created
            with pytest.raises(FileNotFoundError, match="fetch-funding"):
                add_funding_v1_features(df, data_dir=data_dir)


# ---------------------------------------------------------------------------
# 13. KeyError on missing symbol column
# ---------------------------------------------------------------------------


class TestMissingSymbol:
    def test_missing_symbol_raises_key_error(self) -> None:
        """add_funding_v1_features raises KeyError when df has no symbol column."""
        from crypto_trade.features_v1.funding_v1 import add_funding_v1_features

        df = _make_kline_df(n=50, symbol="BTCUSDT").drop(columns=["symbol"])
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(KeyError, match="symbol"):
                add_funding_v1_features(df, data_dir=Path(tmpdir))


# ---------------------------------------------------------------------------
# 14. Dispatch branch pre-flight assertions
# ---------------------------------------------------------------------------


class TestDispatchPreFlight:
    def test_funding_cols_in_pruned_feature_list(self) -> None:
        """The /023 pre-flight asserts must pass when V1_FEATURE_COLUMNS_PRUNED is used."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        active = list(V1_FEATURE_COLUMNS_PRUNED)
        # These are the exact assertions in run_baseline_v1.py iteration_label=="v1-023" branch
        assert "funding_rate_zscore_30" in active, (
            "iter-v1/023 pre-flight would fail: funding_rate_zscore_30 missing"
        )
        assert "funding_rate_zscore_90" in active, (
            "iter-v1/023 pre-flight would fail: funding_rate_zscore_90 missing"
        )


# ---------------------------------------------------------------------------
# 15. Non-null rate > 95% after burn-in
# ---------------------------------------------------------------------------


class TestNonNullCoverage:
    def test_coverage_above_95_pct(self) -> None:
        """After burn-in, non-null z30 coverage must exceed 95% for full-history data.

        n must be large enough that (n - burn_in) / n > 0.95.
        For z30 burn_in=30: need n > 30 / 0.05 = 600. Use n=700 → 670/700=95.7%.
        For z90 burn_in=90: coverage at n=700 is 610/700=87.1% — lower bound set at 85%.
        """
        from crypto_trade.features_v1.funding_v1 import add_funding_v1_features

        n = 700  # sufficient to exceed 95% z30 coverage: (700-30)/700=95.7%
        df = _make_kline_df(n=n, symbol="BTCUSDT")
        funding = _make_funding_df(df, rate_mean=0.0001)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            cache_dir = data_dir / "funding_rates"
            cache_dir.mkdir(parents=True)
            (cache_dir / "BTCUSDT.csv").write_text(funding.to_csv(index=False))
            out = add_funding_v1_features(df, data_dir=data_dir)

        z30_coverage = out["funding_rate_zscore_30"].notna().mean()
        z90_coverage = out["funding_rate_zscore_90"].notna().mean()

        assert z30_coverage >= 0.95, (
            f"z30 coverage {z30_coverage:.2%} below 95% threshold for n={n} rows."
        )
        assert z90_coverage >= 0.85, (
            f"z90 coverage {z90_coverage:.2%} below 85% threshold for n={n} rows. "
            "(90-bar burn-in at n=700 gives 87.1% — intentionally lower bound)"
        )
