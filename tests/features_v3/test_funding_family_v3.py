"""Tests for the v3 funding-rate FEATURE FAMILY — iter-v3/082.

The funding family is a DIFFERENT axis from the closed single
funding_rate_zscore_30 (iter-v3/019/023/024). It builds 4 columns:
funding_sign_persist_9, funding_momentum_3, funding_accel_3,
funding_price_divergence_6.

Focuses on:
1. Past-only discipline — perturbing a future funding rate must not change any
   family value at an earlier bar (the look-ahead invariant).
2. NaN warm-up — the longest-window feature (divergence: 6-bar window + 60-bar
   normalisation + 1-bar shift) determines warm-up.
3. Divergence clip bounds [-10, 10].
4. funding_accel_3 is the exact second difference of funding_momentum_3.
5. GROUP_REGISTRY smoke + FileNotFoundError on missing cache + KeyError on
   missing symbol column.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.funding_v3 import (
    FUNDING_DIVERGENCE_NORM,
    FUNDING_FAMILY_COLUMNS,
    FUNDING_MOMENTUM_WINDOW,
    add_funding_family_v3_features,
    compute_funding_family,
)


def _make_kline_df(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Minimal kline-like DataFrame with open_time + close (8h candles)."""
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
            "volume": rng.uniform(1000, 10000, n),
            "symbol": "BCHUSDT",
        }
    )


def _make_funding_df(n: int = 300, seed: int = 7) -> pd.DataFrame:
    """Funding-rate history aligned to the kline open_times."""
    rng = np.random.default_rng(seed)
    start_ms = 1_679_616_000_000
    interval_ms = 8 * 3600 * 1000
    funding_times = [start_ms + i * interval_ms for i in range(n)]
    # mildly persistent funding (AR-like) to exercise sign-persistence
    rates = np.zeros(n)
    for i in range(1, n):
        rates[i] = 0.7 * rates[i - 1] + rng.normal(0, 0.0003)
    return pd.DataFrame({"funding_time": funding_times, "funding_rate": rates})


def test_all_family_columns_present() -> None:
    """compute_funding_family appends exactly the 4 FUNDING_FAMILY_COLUMNS."""
    out = compute_funding_family(_make_kline_df(), _make_funding_df())
    for col in FUNDING_FAMILY_COLUMNS:
        assert col in out.columns, f"{col} missing"
    assert len(FUNDING_FAMILY_COLUMNS) == 4


def test_past_only_no_lookahead() -> None:
    """Perturbing a FUTURE funding rate must not change any family value at an
    earlier bar. This is the look-ahead invariant — the core discipline test."""
    kline = _make_kline_df(n=300)
    funding = _make_funding_df(n=300)
    base = compute_funding_family(kline, funding)

    perturb_idx = 250  # perturb a late bar
    funding_perturbed = funding.copy()
    funding_perturbed.loc[perturb_idx, "funding_rate"] += 5.0  # huge spike

    perturbed = compute_funding_family(kline, funding_perturbed)

    # every family value at bars STRICTLY BEFORE perturb_idx must be unchanged
    for col in FUNDING_FAMILY_COLUMNS:
        b = base[col].iloc[: perturb_idx - 5]  # margin for the longest window
        p = perturbed[col].iloc[: perturb_idx - 5]
        pd.testing.assert_series_equal(
            b, p, check_names=False,
            obj=f"{col} changed at a bar BEFORE the perturbed future rate",
        )


def test_nan_warmup_divergence() -> None:
    """funding_price_divergence_6 needs 6-bar window + 60-bar norm + 1-bar shift;
    the first ~67 bars should be NaN."""
    out = compute_funding_family(_make_kline_df(n=300), _make_funding_df(n=300))
    div = out["funding_price_divergence_6"]
    warmup = FUNDING_DIVERGENCE_NORM + 6 + 1
    assert div.iloc[: warmup - 5].isna().all(), "divergence has non-NaN inside warm-up"
    assert div.iloc[warmup + 20 :].notna().mean() > 0.9, "divergence too sparse post-warmup"


def test_divergence_clip_bounds() -> None:
    """funding_price_divergence_6 must stay within [-10, 10]."""
    out = compute_funding_family(_make_kline_df(n=400), _make_funding_df(n=400))
    div = out["funding_price_divergence_6"].dropna()
    assert div.min() >= -10.0 - 1e-9
    assert div.max() <= 10.0 + 1e-9


def test_accel_is_second_difference_of_momentum() -> None:
    """funding_accel_3 must equal funding_momentum_3 minus its W-bar lag."""
    out = compute_funding_family(_make_kline_df(n=300), _make_funding_df(n=300))
    mom = out["funding_momentum_3"]
    accel = out["funding_accel_3"]
    expected = mom - mom.shift(FUNDING_MOMENTUM_WINDOW)
    m = accel.notna() & expected.notna()
    assert m.sum() > 100
    np.testing.assert_allclose(
        accel[m].to_numpy(), expected[m].to_numpy(), rtol=1e-9, atol=1e-12
    )


def test_sign_persist_range() -> None:
    """funding_sign_persist_9 is a mean of signs — must lie in [-1, 1]."""
    out = compute_funding_family(_make_kline_df(n=300), _make_funding_df(n=300))
    sp = out["funding_sign_persist_9"].dropna()
    assert sp.min() >= -1.0 - 1e-9
    assert sp.max() <= 1.0 + 1e-9


def test_add_funding_family_registry_entry() -> None:
    """add_funding_family_v3_features reads the per-symbol cache and appends the
    4 columns."""
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        (data_dir / "funding_rates").mkdir()
        _make_funding_df().to_csv(
            data_dir / "funding_rates" / "BCHUSDT.csv", index=False
        )
        out = add_funding_family_v3_features(_make_kline_df(), data_dir=data_dir)
        for col in FUNDING_FAMILY_COLUMNS:
            assert col in out.columns


def test_add_funding_family_missing_cache_raises() -> None:
    """add_funding_family_v3_features raises FileNotFoundError on missing cache."""
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(FileNotFoundError, match="Funding-rate cache not found"):
            add_funding_family_v3_features(_make_kline_df(), data_dir=Path(tmp))


def test_add_funding_family_missing_symbol_raises() -> None:
    """add_funding_family_v3_features raises KeyError without a symbol column."""
    df = _make_kline_df().drop(columns=["symbol"])
    with pytest.raises(KeyError, match="symbol"):
        add_funding_family_v3_features(df)


def test_funding_family_v3_NOT_in_group_registry_for_121_baseline() -> None:
    """funding_family_v3 is NOT registered in /121-minimal GROUP_REGISTRY.

    The funding_family_v3 feature family was tried at iter-v3/082 (cycle-3
    EXPLORATION #1), classified SUSPICIOUS-OOS-DOMINANT, and dropped at /083.
    The module is retained as research museum code (this test file still
    covers the math in isolation) but is NOT in the /121-minimal registry —
    re-adding it would re-introduce a data dependency on
    ``data/funding_rates/<SYM>.csv`` that the /121 baseline does not need.
    """
    from crypto_trade.features_v3 import GROUP_REGISTRY

    assert "funding_family_v3" not in GROUP_REGISTRY
