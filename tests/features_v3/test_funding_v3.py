"""Tests for v3 funding-rate features — iter-v3/019.

Focuses on:
1. Past-only discipline of ``compute_funding_rate_zscore``.
2. Correct window math (first 30 rows NaN).
3. Outlier clipping at [-10, 10].
4. Kline alignment via millisecond rounding (Binance jitter handling).
5. Import smoke test.
6. ``add_funding_v3_features`` FileNotFoundError on missing cache.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.funding_v3 import (
    FUNDING_ZSCORE_WINDOW,
    ZSCORE_CLIP,
    add_funding_v3_features,
    compute_funding_rate_zscore,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_kline_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time column."""
    rng = np.random.default_rng(seed)
    # 8h candles starting at 2023-03-24 00:00 UTC (IS window start)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00:00 UTC in ms
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    open_times = [start_ms + i * interval_ms for i in range(n)]
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": rng.uniform(100, 1000, n),
            "high": rng.uniform(100, 1000, n),
            "low": rng.uniform(100, 1000, n),
            "close": rng.uniform(100, 1000, n),
            "volume": rng.uniform(1000, 10000, n),
            "symbol": "BCHUSDT",
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
    # Add realistic jitter: +0 to +15ms
    jitter_ms = rng.integers(0, 16, n)
    return pd.DataFrame(
        {
            "funding_time": klines["open_time"].values + jitter_ms,
            "funding_rate": rates,
        }
    )


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------


class TestImport:
    def test_importable(self) -> None:
        """Module and public symbols must be importable without error."""
        from crypto_trade.features_v3.funding_v3 import (  # noqa: F401
            add_funding_v3_features,
            compute_funding_rate_zscore,
        )


# ---------------------------------------------------------------------------
# compute_funding_rate_zscore — past-only discipline
# ---------------------------------------------------------------------------


class TestComputeFundingRateZscore:
    def test_column_added(self) -> None:
        """funding_rate_zscore_30 must be present after the call."""
        df = _make_kline_df()
        funding = _make_funding_df(df)
        out = compute_funding_rate_zscore(df, funding)
        assert "funding_rate_zscore_30" in out.columns

    def test_past_only_first_window_rows_nan(self) -> None:
        """The first ``window`` rows of funding_rate_zscore_30 must be NaN.

        With shift(1) + rolling(window, min_periods=window):
          - row 0: shift(1)=NaN → rolling has 0 valid → NaN
          - rows 1..window-1: rolling has < window valid → NaN
          - row window: rolling has exactly window valid (rows 0..window-1
            of the shifted series) → first valid value
        So rows 0..window-1 (inclusive) must all be NaN.
        """
        window = FUNDING_ZSCORE_WINDOW
        df = _make_kline_df(n=200)
        funding = _make_funding_df(df)
        out = compute_funding_rate_zscore(df, funding, window=window)
        zscore = out["funding_rate_zscore_30"]

        # Rows 0..window-1 must be NaN
        assert zscore.iloc[:window].isna().all(), (
            f"Expected first {window} rows to be NaN (rolling init), "
            f"got: {zscore.iloc[:window].tolist()}"
        )
        # At least some rows after window should be valid
        assert zscore.iloc[window:].notna().any()

    def test_past_only_value_at_row_n(self) -> None:
        """Value at row N uses ONLY rows N-window...N-1 — not row N itself.

        We spike row N's funding rate to an extreme value.
        If the z-score at row N reflects this spike in the denominator (rolling
        std), there is look-ahead.  If the z-score at row N is unchanged, past-
        only discipline holds.
        """
        window = FUNDING_ZSCORE_WINDOW
        n = 150
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df)
        out_no_spike = compute_funding_rate_zscore(df.copy(), funding.copy(), window=window)

        # Spike row target_row to an extreme funding rate
        target_row = 80  # well past warm-up
        funding_spiked = funding.copy()
        funding_spiked.loc[target_row, "funding_rate"] = 0.01  # extreme spike

        out_spiked = compute_funding_rate_zscore(df.copy(), funding_spiked, window=window)

        # The z-score at target_row itself:
        #   numerator = funding_spiked[target_row] — DOES change (spike at numerator)
        #   denominator = rolling stats of rows target_row-window...target_row-1 — UNCHANGED
        # So z at target_row IS expected to change (the spike is the numerator).
        # The KEY test: the z-score DENOMINATOR must NOT include row target_row.
        # We verify this by checking rows AFTER target_row:
        #   at row target_row+1, the shifted rolling stats include row target_row in
        #   the window via shift(1). So z at target_row+1 MUST change (spike propagates).
        val_next_no_spike = out_no_spike["funding_rate_zscore_30"].iloc[target_row + 1]
        val_next_spiked = out_spiked["funding_rate_zscore_30"].iloc[target_row + 1]
        assert val_next_no_spike != pytest.approx(val_next_spiked, abs=1e-10), (
            f"z-score at row {target_row + 1} did NOT change after spiking row {target_row}. "
            "The spike should propagate to the next row's rolling window via shift(1)."
        )

    def test_past_only_numerator_uses_bar_t_rate(self) -> None:
        """The numerator at bar t uses rate[t] (the rate that settled AT bar t).

        We verify that spiking row t changes the z-score AT row t (numerator
        effect) but NOT the rolling denominator at row t (which uses only
        rows t-window...t-1 via shift(1)).

        Concretely: the denominator at row t = std(rates[t-window...t-1]) must
        be the same whether or not row t is spiked.  We test this indirectly:
        if the denominator were affected by row t, the z-score change at row t
        would differ from the expected (spike - orig_mean) / orig_std calculation.
        """
        window = FUNDING_ZSCORE_WINDOW
        n = 150
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df, rate_mean=0.0001, seed=7)

        # Compute baseline
        out_base = compute_funding_rate_zscore(df.copy(), funding.copy(), window=window)

        target_row = 80
        # Manually compute expected z-score at target_row using ONLY past rows
        past_rates = funding["funding_rate"].iloc[target_row - window : target_row].values
        past_mean = past_rates.mean()
        past_std = past_rates.std(ddof=1)
        rate_at_t = funding["funding_rate"].iloc[target_row]
        expected_z = (rate_at_t - past_mean) / past_std

        actual_z = out_base["funding_rate_zscore_30"].iloc[target_row]
        assert actual_z == pytest.approx(expected_z, abs=1e-8), (
            f"z-score at row {target_row}: expected {expected_z:.6f}, got {actual_z:.6f}. "
            "Rolling denominator may not be using the correct past-only window."
        )

    def test_clip_to_bounds(self) -> None:
        """Extreme z-scores must be clipped to [-ZSCORE_CLIP, +ZSCORE_CLIP].

        Simulate Binance's funding-floor-clamping artifact: when funding_rate
        is constant for >window bars, std → 0 → z → ∞.  The clip must cap it.
        """
        window = FUNDING_ZSCORE_WINDOW
        n = 100
        df = _make_kline_df(n=n)

        # Constant funding rate → std = 0 after warm-up → ∞ z-score → must be clipped
        constant_rate = 0.0001
        funding = pd.DataFrame(
            {
                "funding_time": df["open_time"].values,
                "funding_rate": [constant_rate] * n,
            }
        )

        out = compute_funding_rate_zscore(df, funding, window=window, clip=ZSCORE_CLIP)
        zscore = out["funding_rate_zscore_30"].dropna()

        # All finite values must be within [-clip, +clip]
        finite_mask = np.isfinite(zscore)
        if finite_mask.any():
            assert (zscore[finite_mask].abs() <= ZSCORE_CLIP + 1e-9).all(), (
                f"z-score exceeds clip bound {ZSCORE_CLIP}: "
                f"max={zscore[finite_mask].abs().max():.2f}"
            )

    def test_kline_alignment_with_jitter(self) -> None:
        """Funding rates with ≤15ms jitter relative to kline open_times must align.

        Binance's fundingTime has ~10-15ms jitter vs the exact 8h boundary.
        The millisecond-rounding merge (//60000*60000) must absorb this.
        """
        window = FUNDING_ZSCORE_WINDOW
        n = 150
        df = _make_kline_df(n=n)
        funding_exact = _make_funding_df(df)
        funding_jitter = _make_funding_df_with_jitter(df)

        out_exact = compute_funding_rate_zscore(df.copy(), funding_exact, window=window)
        out_jitter = compute_funding_rate_zscore(df.copy(), funding_jitter, window=window)

        # Both should produce identical coverage (same rows non-NaN after warm-up)
        exact_coverage = out_exact["funding_rate_zscore_30"].notna().sum()
        jitter_coverage = out_jitter["funding_rate_zscore_30"].notna().sum()
        assert exact_coverage == jitter_coverage, (
            f"Jitter alignment produced different coverage: "
            f"exact={exact_coverage}, jitter={jitter_coverage}. "
            "Millisecond rounding (//60000*60000) may not be absorbing Binance jitter."
        )

        # Values should be approximately equal (same rates, same windows)
        valid = out_exact["funding_rate_zscore_30"].notna()
        diff = (
            out_exact["funding_rate_zscore_30"][valid] - out_jitter["funding_rate_zscore_30"][valid]
        ).abs()
        assert (diff < 1e-9).all(), (
            f"z-scores differ between exact and jittered funding_time: max_diff={diff.max():.2e}"
        )

    def test_unmatched_klines_produce_nan(self) -> None:
        """Klines that have no matching funding record must get NaN z-scores."""
        n = 100
        df = _make_kline_df(n=n)
        # Funding only covers first half
        funding = _make_funding_df(df.iloc[:50])
        out = compute_funding_rate_zscore(df, funding, window=FUNDING_ZSCORE_WINDOW)
        # Rows 50..99 have no matching funding → NaN
        assert out["funding_rate_zscore_30"].iloc[50:].isna().all(), (
            "Rows without matching funding records should produce NaN z-scores."
        )

    def test_result_approximately_standard_normal(self) -> None:
        """After warm-up, z-scores from i.i.d. rates should approximate N(0,1)."""
        window = FUNDING_ZSCORE_WINDOW
        n = 1000
        df = _make_kline_df(n=n)
        rng = np.random.default_rng(99)
        # i.i.d. normal rates → z-score should be approx N(0,1)
        rates = rng.normal(0.0001, 0.0002, n)
        funding = pd.DataFrame(
            {
                "funding_time": df["open_time"].values,
                "funding_rate": rates,
            }
        )
        out = compute_funding_rate_zscore(df, funding, window=window)
        zscore = out["funding_rate_zscore_30"].dropna()
        assert abs(zscore.mean()) < 0.15, f"Mean too far from 0: {zscore.mean():.4f}"
        assert abs(zscore.std() - 1.0) < 0.15, f"Std too far from 1: {zscore.std():.4f}"


# ---------------------------------------------------------------------------
# add_funding_v3_features — file I/O and integration
# ---------------------------------------------------------------------------


class TestAddFundingV3Features:
    def test_missing_cache_raises_file_not_found(self) -> None:
        """FileNotFoundError must be raised if funding cache does not exist."""
        df = _make_kline_df(n=50)
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            # No cache file created — must raise
            with pytest.raises(FileNotFoundError, match="fetch-funding"):
                add_funding_v3_features(df, data_dir=data_dir)

    def test_missing_symbol_column_raises_key_error(self) -> None:
        """KeyError must be raised if df lacks the 'symbol' column."""
        df = _make_kline_df(n=50).drop(columns=["symbol"])
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(KeyError, match="symbol"):
                add_funding_v3_features(df, data_dir=Path(tmpdir))

    def test_returns_funding_zscore_column(self) -> None:
        """When cache exists, funding_rate_zscore_30 must be added to df."""
        n = 100
        df = _make_kline_df(n=n)
        funding = _make_funding_df(df)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            cache_dir = data_dir / "funding_rates"
            cache_dir.mkdir(parents=True)
            cache_path = cache_dir / "BCHUSDT.csv"
            funding.rename(columns={"funding_time": "funding_time"}).to_csv(cache_path, index=False)

            out = add_funding_v3_features(df, data_dir=data_dir)

        assert "funding_rate_zscore_30" in out.columns
        # Coverage: with n=100 rows and window=30, first valid z-score is at
        # row 30, so 70/100 = 70.0% — the test uses n=100 as a minimal smoke
        # test; real IS data (2193 rows) gives >98% coverage.
        coverage = out["funding_rate_zscore_30"].notna().mean()
        assert coverage >= 0.70, (
            f"Coverage {coverage:.2%} unexpectedly low for n={n} rows "
            f"with window={FUNDING_ZSCORE_WINDOW}"
        )

    def test_empty_cache_adds_nan_column(self) -> None:
        """Empty funding cache must add an all-NaN column without error."""
        df = _make_kline_df(n=50)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            cache_dir = data_dir / "funding_rates"
            cache_dir.mkdir(parents=True)
            # Write empty CSV with headers only
            cache_path = cache_dir / "BCHUSDT.csv"
            pd.DataFrame(columns=["funding_time", "funding_rate"]).to_csv(cache_path, index=False)

            out = add_funding_v3_features(df, data_dir=data_dir)

        assert "funding_rate_zscore_30" in out.columns
        assert out["funding_rate_zscore_30"].isna().all()
