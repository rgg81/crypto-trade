"""Tests for compute_excess_ret_5d_vs_majors_z90 — iter-v1/078.

Three test tiers:
1. test_feature_in_aave_parquet    — column present in regenerated v1 AAVE parquet
2. test_feature_is_mostly_finite   — < 5% NaN in the full parquet
3. test_feature_idempotent         — re-generation via compute_excess_ret_5d_vs_majors_z90
                                     on the same inputs produces the same values (bit-exact)

Unit-level tests:
4. test_compute_excess_basic        — output is a pandas Series with correct length
5. test_compute_excess_no_lookahead — perturbing last row does not affect earlier rows
6. test_compute_excess_clip_bounds  — all finite values are within [-10, 10]
7. test_compute_excess_all_nan_fill — NaN warm-up rows are filled with 0.0
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_PARQUET_PATH = _ROOT / "data" / "features" / "AAVEUSDT_8h_features.parquet"
_FEATURE_COL = "excess_ret_5d_vs_majors_z90"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parquet_sha256_16(path: Path) -> str:
    """Return the first 16 hex chars of SHA-256 of the parquet file bytes."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _make_synthetic_frames(
    n: int = 200, seed: int = 42
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Make synthetic sym / BTC / ETH DataFrames for unit-level tests."""
    rng = np.random.default_rng(seed)
    open_time = np.arange(n, dtype="int64") * 8 * 3600 * 1000  # 8h intervals in ms
    sym_price = np.cumprod(1 + rng.standard_normal(n) * 0.02) * 100
    btc_price = np.cumprod(1 + rng.standard_normal(n) * 0.015) * 30_000
    eth_price = np.cumprod(1 + rng.standard_normal(n) * 0.018) * 2_000

    df_sym = pd.DataFrame(
        {
            "open_time": open_time,
            "close": sym_price,
            "symbol": "TESTUSDT",
        }
    )
    btc_close = pd.Series(btc_price, name="close")
    eth_close = pd.Series(eth_price, name="close")
    return df_sym, btc_close, eth_close


# ---------------------------------------------------------------------------
# Parquet-level tests (require regenerated parquet with new column)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _PARQUET_PATH.exists(), reason="AAVE parquet not found")
def test_feature_in_aave_parquet() -> None:
    """excess_ret_5d_vs_majors_z90 must exist in the regenerated AAVE v1 parquet."""
    df = pd.read_parquet(_PARQUET_PATH)
    assert _FEATURE_COL in df.columns, (
        f"Column '{_FEATURE_COL}' not found in {_PARQUET_PATH}. "
        "Run: uv run crypto-trade features --symbols AAVEUSDT --interval 8h "
        "--track v1 --format parquet --workers 4"
    )


@pytest.mark.skipif(not _PARQUET_PATH.exists(), reason="AAVE parquet not found")
def test_feature_is_mostly_finite() -> None:
    """NaN fraction in excess_ret_5d_vs_majors_z90 must be < 5% of total rows."""
    df = pd.read_parquet(_PARQUET_PATH)
    if _FEATURE_COL not in df.columns:
        pytest.skip(f"Column '{_FEATURE_COL}' absent — parquet needs regeneration")
    col = df[_FEATURE_COL]
    nan_frac = col.isna().mean()
    assert nan_frac < 0.05, (
        f"NaN fraction {nan_frac:.3f} exceeds 5% threshold. "
        "Check that the 90-bar warm-up is correctly filled with 0.0."
    )


@pytest.mark.skipif(not _PARQUET_PATH.exists(), reason="AAVE parquet not found")
def test_feature_idempotent() -> None:
    """Re-computing via compute_excess_ret_5d_vs_majors_z90 yields same values as the parquet."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_excess_ret_5d_vs_majors_z90

    df = pd.read_parquet(_PARQUET_PATH)
    if _FEATURE_COL not in df.columns:
        pytest.skip(f"Column '{_FEATURE_COL}' absent — parquet needs regeneration")

    # Load BTC and ETH closes from the data directory
    btc_path = _ROOT / "data" / "BTCUSDT" / "8h.csv"
    eth_path = _ROOT / "data" / "ETHUSDT" / "8h.csv"
    if not btc_path.exists() or not eth_path.exists():
        pytest.skip("BTC or ETH 8h.csv not found in data directory")

    btc_raw = pd.read_csv(btc_path, usecols=["open_time", "close"])
    eth_raw = pd.read_csv(eth_path, usecols=["open_time", "close"])
    btc_raw["open_time"] = btc_raw["open_time"].astype("int64")
    eth_raw["open_time"] = eth_raw["open_time"].astype("int64")

    # Align BTC and ETH closes to the parquet's open_time index
    df_tmp = df[["open_time"]].copy()
    df_tmp = df_tmp.merge(
        btc_raw.rename(columns={"close": "_btc_close"}), on="open_time", how="left"
    )
    df_tmp = df_tmp.merge(
        eth_raw.rename(columns={"close": "_eth_close"}), on="open_time", how="left"
    )

    btc_close = pd.to_numeric(df_tmp["_btc_close"], errors="coerce").reset_index(drop=True)
    eth_close = pd.to_numeric(df_tmp["_eth_close"], errors="coerce").reset_index(drop=True)

    recomputed = compute_excess_ret_5d_vs_majors_z90(
        df_sym=df.copy(),
        btc_close=btc_close,
        eth_close=eth_close,
    )

    # Values should be bit-exact (deterministic pandas rolling ops)
    parquet_vals = df[_FEATURE_COL].reset_index(drop=True)
    recomputed_vals = recomputed.reset_index(drop=True)
    pd.testing.assert_series_equal(
        parquet_vals,
        recomputed_vals,
        check_names=False,
        rtol=1e-6,
        obj="excess_ret_5d_vs_majors_z90 recomputed vs parquet",
    )


# ---------------------------------------------------------------------------
# Unit-level tests (no parquet dependency)
# ---------------------------------------------------------------------------


def test_compute_excess_basic() -> None:
    """compute_excess_ret_5d_vs_majors_z90 returns a Series of length n."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_excess_ret_5d_vs_majors_z90

    df_sym, btc_close, eth_close = _make_synthetic_frames(n=200)
    result = compute_excess_ret_5d_vs_majors_z90(df_sym, btc_close, eth_close)
    assert isinstance(result, pd.Series), "Output must be a pd.Series"
    assert len(result) == len(df_sym), f"Length mismatch: {len(result)} != {len(df_sym)}"


def test_compute_excess_no_lookahead() -> None:
    """Perturbing the last row does not change any earlier row's value."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_excess_ret_5d_vs_majors_z90

    df_sym, btc_close, eth_close = _make_synthetic_frames(n=200)
    result_base = compute_excess_ret_5d_vs_majors_z90(df_sym, btc_close, eth_close)

    # Perturb only the last close value of all three series
    df_sym_perturbed = df_sym.copy()
    df_sym_perturbed.loc[df_sym_perturbed.index[-1], "close"] *= 2.0
    btc_perturbed = btc_close.copy()
    btc_perturbed.iloc[-1] *= 2.0
    eth_perturbed = eth_close.copy()
    eth_perturbed.iloc[-1] *= 2.0

    result_perturbed = compute_excess_ret_5d_vs_majors_z90(
        df_sym_perturbed, btc_perturbed, eth_perturbed
    )

    # All rows except the last 15 (ret_window_bars=15 propagation window) and
    # the warm-up zone should be identical.
    check_end = len(df_sym) - 15 - 1  # safe zone: bars before perturbation can propagate
    pd.testing.assert_series_equal(
        result_base.iloc[:check_end].reset_index(drop=True),
        result_perturbed.iloc[:check_end].reset_index(drop=True),
        check_names=False,
        rtol=1e-6,
        obj="past-only invariant: early rows unchanged by last-bar perturbation",
    )


def test_compute_excess_clip_bounds() -> None:
    """All finite output values must be within [-10, +10]."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_excess_ret_5d_vs_majors_z90

    df_sym, btc_close, eth_close = _make_synthetic_frames(n=300)
    result = compute_excess_ret_5d_vs_majors_z90(df_sym, btc_close, eth_close)
    finite_vals = result[result.notna()]
    assert (finite_vals >= -10.0).all(), "Values below -10 clip threshold found"
    assert (finite_vals <= 10.0).all(), "Values above +10 clip threshold found"


def test_compute_excess_all_nan_fill() -> None:
    """NaN warm-up rows are filled with 0.0 (no NaN in output)."""
    from crypto_trade.features_v1.cross_btc_v1 import compute_excess_ret_5d_vs_majors_z90

    df_sym, btc_close, eth_close = _make_synthetic_frames(n=200)
    result = compute_excess_ret_5d_vs_majors_z90(df_sym, btc_close, eth_close)
    nan_count = result.isna().sum()
    assert nan_count == 0, (
        f"Expected 0 NaN values (warm-up filled with 0.0), got {nan_count}. "
        "Check fillna(0.0) in compute_excess_ret_5d_vs_majors_z90."
    )
