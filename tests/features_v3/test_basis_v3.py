"""Tests for the v3 perp-spot BASIS feature family — iter-v3/086.

The basis family is a NEW crypto-native data feed (cycle-3 EXPLORATION #5). It
builds 3 columns from basis = (perp_close - spot_close) / spot_close:
basis_zscore_30, basis_momentum_3, basis_extreme_flag.

Focuses on:
1. Past-only discipline — perturbing a FUTURE perp close must not change any
   basis feature at an earlier bar (the look-ahead invariant; basis features
   are computed on basis.shift(1) — a strict one-candle lag).
2. basis_zscore_30 clip bounds [-10, 10].
3. NaN warm-up — the 30-bar z-score + 1-bar shift determines warm-up.
4. The 3 BASIS_FAMILY_COLUMNS are appended; raw `close` is preserved.
5. GROUP_REGISTRY smoke + FileNotFoundError on missing cache + KeyError on
   missing symbol column.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.basis_v3 import (
    BASIS_FAMILY_COLUMNS,
    BASIS_ZSCORE_WINDOW,
    add_basis_v3_features,
    compute_basis_features,
)


def _make_perp_df(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Minimal perp kline-like DataFrame with open_time + close (8h candles)."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000  # 2023-03-24 00:00:00 UTC
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    close = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.02, n))
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1e3, 1e4, n),
        }
    )


def _make_spot_df(perp: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """Spot frame: same open_times, spot close = perp close * (1 + small noise)."""
    rng = np.random.default_rng(seed)
    spot_close = perp["close"].to_numpy() * (1.0 + rng.normal(0, 0.001, len(perp)))
    return pd.DataFrame({"open_time": perp["open_time"].to_numpy(), "close": spot_close})


def test_basis_columns_appended_and_close_preserved() -> None:
    perp = _make_perp_df()
    spot = _make_spot_df(perp)
    out = compute_basis_features(perp, spot)
    for col in BASIS_FAMILY_COLUMNS:
        assert col in out.columns, f"{col} missing from output"
    # raw perp `close` must be preserved unchanged
    pd.testing.assert_series_equal(out["close"], perp["close"])
    # the merge helper column must NOT leak into the output
    assert "_spot_close" not in out.columns


def test_past_only_no_lookahead() -> None:
    """Perturb perp_close at bar K; assert all basis features at bars < K are
    bit-identical, and the perturbation propagates at/after bar K."""
    perp = _make_perp_df(n=300)
    spot = _make_spot_df(perp)
    base = compute_basis_features(perp, spot)

    k = 250
    perturbed = perp.copy()
    perturbed.loc[k, "close"] = float(perturbed.loc[k, "close"]) * 1.5  # +50% spike
    pert = compute_basis_features(perturbed, spot)

    for col in BASIS_FAMILY_COLUMNS:
        b0 = base[col].to_numpy()[:k]
        b1 = pert[col].to_numpy()[:k]
        both_nan = np.isnan(b0) & np.isnan(b1)
        assert np.all(both_nan | (b0 == b1)), f"{col} changed at a bar < {k} — look-ahead leak"
    # the perturbation MUST propagate somewhere at/after bar k (sanity: the
    # feature actually depends on the perturbed close).
    z0 = base["basis_zscore_30"].to_numpy()[k:]
    z1 = pert["basis_zscore_30"].to_numpy()[k:]
    diff = ~(np.isnan(z0) & np.isnan(z1)) & (z0 != z1)
    assert diff.any(), "perturbation did not propagate — feature is inert"


def test_basis_zscore_clip_bounds() -> None:
    perp = _make_perp_df(n=300)
    spot = _make_spot_df(perp)
    out = compute_basis_features(perp, spot)
    z = out["basis_zscore_30"].dropna()
    assert (z >= -10.0).all() and (z <= 10.0).all(), "basis_zscore_30 outside clip"


def test_nan_warmup() -> None:
    perp = _make_perp_df(n=300)
    spot = _make_spot_df(perp)
    out = compute_basis_features(perp, spot)
    # basis_zscore_30: 1-bar shift + 30-bar window -> first ~31 rows NaN.
    z = out["basis_zscore_30"]
    assert z.iloc[:BASIS_ZSCORE_WINDOW].isna().all()
    assert z.iloc[BASIS_ZSCORE_WINDOW + 5 :].notna().any()


def test_group_registry_smoke(tmp_path: Path) -> None:
    """add_basis_v3_features reads data/spot/<SYM>/8h.csv via the data_dir arg."""
    perp = _make_perp_df()
    spot = _make_spot_df(perp)
    perp = perp.assign(symbol="BCHUSDT")

    spot_dir = tmp_path / "spot" / "BCHUSDT"
    spot_dir.mkdir(parents=True)
    spot.to_csv(spot_dir / "8h.csv", index=False)

    out = add_basis_v3_features(perp, data_dir=tmp_path)
    for col in BASIS_FAMILY_COLUMNS:
        assert col in out.columns


def test_missing_cache_raises() -> None:
    perp = _make_perp_df().assign(symbol="BCHUSDT")
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(FileNotFoundError, match="Spot-kline cache not found"):
            add_basis_v3_features(perp, data_dir=Path(td))


def test_missing_symbol_column_raises() -> None:
    perp = _make_perp_df()  # no 'symbol' column
    with pytest.raises(KeyError, match="must contain a 'symbol' column"):
        add_basis_v3_features(perp)


def test_basis_genuinely_distinct_from_close() -> None:
    """The basis is perp-vs-spot, not a price feature: with spot == perp the
    basis is identically zero (degenerate) — confirms the feature is the
    perp-spot SPREAD, not a repackaged price level."""
    perp = _make_perp_df()
    spot_eq = pd.DataFrame(
        {"open_time": perp["open_time"].to_numpy(), "close": perp["close"].to_numpy()}
    )
    out = compute_basis_features(perp, spot_eq)
    # basis == 0 everywhere -> momentum == 0; z-score is NaN (std of zeros -> 0).
    mom = out["basis_momentum_3"].dropna()
    assert np.allclose(mom, 0.0), "basis_momentum_3 should be 0 when spot == perp"
