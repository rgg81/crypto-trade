"""Tests for v3 volume-microstructure features — iter-v3/015.

Focuses on ``compute_tbr_zscore`` look-ahead discipline:
- First ``window`` rows must be NaN (rolling-window initialization).
- Value at row N depends only on rows N-window...N-1 (past-only, .shift(1)).
- Function is importable and returns the expected column names.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.volume_micro_v3 import compute_tbr_zscore


def _make_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Create a minimal kline-like DataFrame for testing."""
    rng = np.random.default_rng(seed)
    quote_volume = rng.uniform(1_000, 10_000, size=n)
    taker_buy_fraction = rng.uniform(0.3, 0.7, size=n)
    taker_buy_quote_volume = quote_volume * taker_buy_fraction
    return pd.DataFrame(
        {
            "quote_volume": quote_volume,
            "taker_buy_quote_volume": taker_buy_quote_volume,
        }
    )


class TestComputeTbrZscore:
    def test_columns_added(self) -> None:
        """Both tbr_raw and tbr_zscore_30 must be present after the call."""
        df = _make_df()
        out = compute_tbr_zscore(df)
        assert "tbr_raw" in out.columns
        assert "tbr_zscore_30" in out.columns

    def test_past_only_first_window_rows_nan(self) -> None:
        """The first ``window`` rows of tbr_zscore_30 must be NaN.

        With shift(1) + rolling(window, min_periods=window):
          - row 0: s.shift(1) = NaN -> rolling has 0 valid -> NaN
          - rows 1..window-1: rolling has < window valid -> NaN
          - row window: rolling has exactly window valid (rows 0..window-1
            of the shifted series) -> first valid value
        So rows 0..window-1 (inclusive) should be NaN.
        """
        window = 30
        df = _make_df(n=200)
        out = compute_tbr_zscore(df, window=window)
        zscore = out["tbr_zscore_30"]
        # Rows 0 .. window-1 (inclusive) = first window rows must be NaN
        assert zscore.iloc[:window].isna().all(), (
            f"Expected first {window} rows to be NaN (rolling init), "
            f"but got: {zscore.iloc[:window].tolist()}"
        )
        # At least some rows after window should be valid
        assert zscore.iloc[window:].notna().any()

    def test_past_only_value_at_row_n(self) -> None:
        """Value at row N uses ONLY rows N-window...N-1 — not row N itself.

        We spike row N's taker_buy_quote_volume to an extreme value.
        If the z-score at row N reflects this spike, there is look-ahead.
        If the z-score at row N is unchanged, past-only discipline holds.
        """
        window = 30
        n = 100
        df = _make_df(n=n)
        out_no_spike = compute_tbr_zscore(df.copy(), window=window)

        # Spike row N (an interior row well past warm-up)
        target_row = 60
        df_spiked = df.copy()
        # Set taker_buy to 99.9% of quote_volume (extreme spike at row target_row)
        df_spiked.loc[target_row, "taker_buy_quote_volume"] = (
            df_spiked.loc[target_row, "quote_volume"] * 0.999
        )
        out_spiked = compute_tbr_zscore(df_spiked, window=window)

        # The z-score at target_row itself must NOT change — it uses only past rows
        val_no_spike = out_no_spike["tbr_zscore_30"].iloc[target_row]
        val_spiked = out_spiked["tbr_zscore_30"].iloc[target_row]
        assert val_no_spike == pytest.approx(val_spiked, abs=1e-10), (
            f"z-score at row {target_row} changed after spiking row {target_row}: "
            f"no_spike={val_no_spike:.6f}, spiked={val_spiked:.6f}. "
            "This indicates look-ahead: row's own value was used in its z-score."
        )

        # But the z-score at target_row + 1 SHOULD change (the spike now enters
        # the past window via shift(1))
        val_next_no_spike = out_no_spike["tbr_zscore_30"].iloc[target_row + 1]
        val_next_spiked = out_spiked["tbr_zscore_30"].iloc[target_row + 1]
        assert val_next_no_spike != pytest.approx(val_next_spiked, abs=1e-10), (
            f"z-score at row {target_row + 1} did NOT change after spiking row {target_row}: "
            f"no_spike={val_next_no_spike:.6f}, spiked={val_next_spiked:.6f}. "
            "The spike should propagate to the next row's window."
        )

    def test_zero_quote_volume_gives_nan(self) -> None:
        """Rows where quote_volume == 0 must produce NaN tbr_raw (and NaN z-score)."""
        df = _make_df(n=100)
        df.loc[50, "quote_volume"] = 0.0
        df.loc[50, "taker_buy_quote_volume"] = 0.0
        out = compute_tbr_zscore(df)
        assert np.isnan(out["tbr_raw"].iloc[50])

    def test_tbr_raw_in_unit_interval(self) -> None:
        """tbr_raw must be in [0, 1] for rows with positive quote_volume."""
        df = _make_df(n=150)
        out = compute_tbr_zscore(df)
        valid = out["tbr_raw"].dropna()
        assert (valid >= 0).all() and (valid <= 1).all()

    def test_zscore_approximately_standard_normal(self) -> None:
        """After warm-up, tbr_zscore_30 should be approximately N(0,1)."""
        window = 30
        df = _make_df(n=500)
        out = compute_tbr_zscore(df, window=window)
        zscore = out["tbr_zscore_30"].dropna()
        assert abs(zscore.mean()) < 0.2, f"Mean too far from 0: {zscore.mean():.4f}"
        assert abs(zscore.std() - 1.0) < 0.2, f"Std too far from 1: {zscore.std():.4f}"
