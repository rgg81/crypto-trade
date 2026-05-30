"""Tests for v1 basis features — iter-v1/034.

Covers:
1.  test_compute_basis_zscore_past_only — bar t's own basis_bps does NOT enter its
    own rolling denominator (lookahead guard — per /027 LESSON).
2.  test_compute_basis_zscore_known_values — hand-computed z-score on a 32-row
    synthetic series matches compute_basis_zscore output to <1e-9.
3.  test_compute_basis_zscore_clip — outlier basis_bps (>10000 bps) gets clipped
    to ±10.0 in z output.
4.  test_compute_basis_zscore_burn_in_nan — first window-1 rows are NaN (rolling warm-up).
5.  test_add_basis_v1_features_missing_spot_raises — FileNotFoundError raised when
    spot CSV missing.
6.  test_add_basis_v1_features_btc_smoke — runs on real BTC data; output has
    basis_zscore_30 column; non-null fraction > 95% after burn-in.
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


def _make_perp_df(
    n: int = 60,
    seed: int = 42,
    symbol: str = "BTCUSDT",
    close_start: float = 50_000.0,
) -> pd.DataFrame:
    """Create a minimal perp kline DataFrame with open_time, close, symbol."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00 UTC
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    closes = close_start + np.cumsum(rng.normal(0, 100, n))
    return pd.DataFrame(
        {
            "open_time": open_times,
            "close": closes,
            "symbol": symbol,
        }
    )


def _make_spot_df(
    perp_df: pd.DataFrame,
    basis_bps_values: np.ndarray | None = None,
) -> pd.DataFrame:
    """Create a spot DataFrame aligned to perp_df, with optional basis_bps control."""
    spot = perp_df[["open_time"]].copy()
    perp_close = perp_df["close"].values
    if basis_bps_values is None:
        # Default: ~10 bps offset (small positive basis)
        spot_close = perp_close / (1.0 + 10.0 / 10_000.0)
    else:
        # Construct spot_close to produce the requested basis_bps
        # basis_bps = (perp - spot) / spot * 10000
        # => spot = perp / (1 + basis_bps / 10000)
        spot_close = perp_close / (1.0 + basis_bps_values / 10_000.0)
    spot["close"] = spot_close
    return spot


# ---------------------------------------------------------------------------
# Test 1 — Past-only invariant (no lookahead)
# ---------------------------------------------------------------------------


def test_compute_basis_zscore_past_only() -> None:
    """Bar t's own basis_bps must NOT enter its own rolling denominator.

    Mechanism: we inject a single-bar spike at position 31 (first non-NaN z-score
    position after 30-bar burn-in). If the spike leaked into bar 31's own rolling
    stats, the z-score at bar 31 would be near 0.0 (self-mean-centered). A correct
    past-only implementation produces a large z-score at bar 31 because bar 31's
    basis_bps is far outside the [t-30..t-1] window.
    """
    from crypto_trade.features_v1.basis_v1 import compute_basis_zscore

    n = 60
    window = 30

    # Flat basis at 10 bps for bars 0..30, then a large spike at bar 31
    basis_bps = np.full(n, 10.0)
    basis_bps[31] = 10_000.0  # +10000 bps spike — far outside normal range

    perp_df = _make_perp_df(n=n)
    spot_df = _make_spot_df(perp_df, basis_bps_values=basis_bps)

    result = compute_basis_zscore(perp_df, spot_df, window=window, clip=100.0)

    z = result["basis_zscore_30"].values

    # Bar 31: spike is in the NUMERATOR (basis_bps[31] = 10000).
    # Rolling stats at bar 31 use only bars [1..30] (via shift(1)), all at ~10 bps.
    # So z[31] should be very large (>> 1), NOT near 0.0.
    assert z[31] > 5.0, (
        f"Bar 31 z-score should be large (spike in numerator, NOT in denominator). "
        f"Got z[31]={z[31]:.4f}. If near 0, lookahead is present."
    )

    # Bars 1..30: NaN (burn-in window)
    assert all(np.isnan(z[1:window])), "Bars 1..window-1 should be NaN (burn-in)"

    # Bar 0: NaN (shift(1) makes first shifted bar NaN → NaN rolling stats)
    assert np.isnan(z[0]), "Bar 0 should be NaN (shift(1) creates NaN at position 0)"


# ---------------------------------------------------------------------------
# Test 2 — Known-values correctness
# ---------------------------------------------------------------------------


def test_compute_basis_zscore_known_values() -> None:
    """Hand-computed z-score on a 32-row synthetic series matches output to <1e-9."""
    from crypto_trade.features_v1.basis_v1 import compute_basis_zscore

    window = 30
    n = 32

    # Known basis_bps: constant 5.0 for bars 0..30, then 8.0 at bar 31
    basis_bps = np.full(n, 5.0)
    basis_bps[31] = 8.0

    perp_df = _make_perp_df(n=n, close_start=50_000.0)
    # Fix perp close to 50000 for exact computation
    perp_df["close"] = 50_000.0
    spot_df = _make_spot_df(perp_df, basis_bps_values=basis_bps)

    result = compute_basis_zscore(perp_df, spot_df, window=window, clip=100.0)
    z = result["basis_zscore_30"].values

    # At bar 31: rolling window covers shift(1) → bars [1..30] all at 5.0 bps.
    # mean = 5.0, std(ddof=1) = 0.0 (constant series).
    # std = 0 → z-score uses rstd.replace(0, NaN) → z[31] is NaN.
    # This tests the zero-std guard: constant series → NaN z-score.
    assert np.isnan(z[31]), (
        f"Constant basis series should produce NaN z-score (std=0 → replace). Got z[31]={z[31]}"
    )

    # Now use a series with slight variation to test the math directly.
    rng = np.random.default_rng(99)
    varied_bps = 5.0 + rng.normal(0, 1.0, n)
    varied_bps[31] = 9.0  # spike

    perp_df2 = _make_perp_df(n=n, close_start=50_000.0)
    perp_df2["close"] = 50_000.0
    spot_df2 = _make_spot_df(perp_df2, basis_bps_values=varied_bps)

    result2 = compute_basis_zscore(perp_df2, spot_df2, window=window, clip=100.0)
    z2 = result2["basis_zscore_30"].values

    # Hand-compute z[31]: window covers bars [1..30] (shift(1) → bars 0..29 shifted)
    # Rolling uses s_shifted = basis_bps.shift(1), so at bar 31 it uses bars [1..30]
    s_shifted_hand = np.concatenate([[np.nan], varied_bps[:-1]])  # shift(1)
    # pandas rolling at index 31 with window=30 uses the last 30 values of the shifted series
    # Recalculate using pandas logic:
    s_s = pd.Series(s_shifted_hand)
    hand_mean = s_s.rolling(window=window, min_periods=window).mean().iloc[31]
    hand_std = s_s.rolling(window=window, min_periods=window).std(ddof=1).iloc[31]
    hand_z = (varied_bps[31] - hand_mean) / hand_std

    # Verify match to <1e-9
    assert abs(z2[31] - hand_z) < 1e-9, (
        f"Known-value mismatch: computed z={z2[31]:.12f}, "
        f"hand_computed z={hand_z:.12f}, diff={abs(z2[31] - hand_z):.2e}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Clip enforcement
# ---------------------------------------------------------------------------


def test_compute_basis_zscore_clip() -> None:
    """Outlier basis_bps (extreme spike) gets clipped to ±10.0 in z output."""
    from crypto_trade.features_v1.basis_v1 import compute_basis_zscore

    window = 30
    n = 70

    rng = np.random.default_rng(77)
    basis_bps = rng.normal(0, 2.0, n)
    # Insert a catastrophic spike that would produce z >> 10
    basis_bps[50] = 1_000_000.0  # effectively infinity in z-score space

    perp_df = _make_perp_df(n=n)
    spot_df = _make_spot_df(perp_df, basis_bps_values=basis_bps)

    result = compute_basis_zscore(perp_df, spot_df, window=window, clip=10.0)
    z = result["basis_zscore_30"].values

    non_nan = z[~np.isnan(z)]
    assert np.all(non_nan <= 10.0), f"z-score exceeds +10 clip: max={non_nan.max():.2f}"
    assert np.all(non_nan >= -10.0), f"z-score below -10 clip: min={non_nan.min():.2f}"
    # The spike bar itself should be clipped to +10.0
    assert z[50] == pytest.approx(10.0, abs=1e-9), (
        f"Spike bar z[50] should be clipped to +10.0, got {z[50]}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Burn-in NaN
# ---------------------------------------------------------------------------


def test_compute_basis_zscore_burn_in_nan() -> None:
    """First window-1 rows should be NaN due to rolling warm-up."""
    from crypto_trade.features_v1.basis_v1 import compute_basis_zscore

    window = 30
    n = 80
    rng = np.random.default_rng(12)
    basis_bps = rng.normal(10, 3.0, n)

    perp_df = _make_perp_df(n=n)
    spot_df = _make_spot_df(perp_df, basis_bps_values=basis_bps)

    result = compute_basis_zscore(perp_df, spot_df, window=window, clip=10.0)
    z = result["basis_zscore_30"].values

    # Bars 0..window-1: NaN (burn-in; shift(1) + rolling with min_periods=window)
    # Specifically: bars 0..30 are NaN (bar 30 is the first bar with 30 prior shifted vals)
    assert all(np.isnan(z[:window])), (
        f"First {window} bars should be NaN; got non-NaN at "
        f"{[i for i in range(window) if not np.isnan(z[i])]}"
    )
    # Bar 30+: should start having values
    assert not np.isnan(z[window]), (
        f"Bar {window} should be non-NaN after burn-in (rolling window complete)"
    )


# ---------------------------------------------------------------------------
# Test 5 — Missing spot CSV raises FileNotFoundError
# ---------------------------------------------------------------------------


def test_add_basis_v1_features_missing_spot_raises() -> None:
    """FileNotFoundError raised when spot CSV missing."""
    from crypto_trade.features_v1.basis_v1 import add_basis_v1_features

    perp_df = _make_perp_df(n=50)
    perp_df["symbol"] = "BTCUSDT"

    with tempfile.TemporaryDirectory() as tmpdir:
        # data_dir/spot/BTCUSDT/8h.csv does NOT exist
        with pytest.raises(FileNotFoundError, match="Spot kline CSV not found"):
            add_basis_v1_features(perp_df, data_dir=tmpdir)


# ---------------------------------------------------------------------------
# Test 6 — Real BTC data smoke test
# ---------------------------------------------------------------------------


def test_add_basis_v1_features_btc_smoke() -> None:
    """Runs on real BTC perp + spot data; output has basis_zscore_30 column;
    non-null fraction > 95% after burn-in."""
    from crypto_trade.features_v1.basis_v1 import add_basis_v1_features

    # Real perp data location (standard worktree layout)
    perp_path = Path("data/BTCUSDT/8h.csv")
    spot_path = Path("data/spot/BTCUSDT/8h.csv")

    if not perp_path.exists() or not spot_path.exists():
        pytest.skip("Real BTC perp or spot 8h data not available in this worktree")

    perp_df = pd.read_csv(perp_path)
    perp_df["symbol"] = "BTCUSDT"
    # Ensure close is numeric
    perp_df["close"] = pd.to_numeric(perp_df["close"], errors="coerce")
    perp_df["open_time"] = perp_df["open_time"].astype("int64")

    result = add_basis_v1_features(perp_df, data_dir=Path("data"))

    # Output column present
    assert "basis_zscore_30" in result.columns, "basis_zscore_30 column missing from output"

    # Non-null fraction after burn-in (skip first 30 rows)
    after_burnin = result["basis_zscore_30"].iloc[30:]
    non_null_frac = after_burnin.notna().mean()
    assert non_null_frac > 0.95, (
        f"basis_zscore_30 non-null fraction after burn-in should be >95%; got {non_null_frac:.3f}"
    )

    # Clip check: all non-NaN values within [-10, 10]
    non_nan_vals = after_burnin.dropna()
    assert non_nan_vals.max() <= 10.0, f"Max z-score {non_nan_vals.max()} exceeds +10 clip"
    assert non_nan_vals.min() >= -10.0, f"Min z-score {non_nan_vals.min()} below -10 clip"
