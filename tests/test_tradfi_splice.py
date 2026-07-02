"""Leak-safety + IS-bit-identical asserts for the Yahoo->perp spliced tradfi loader.

Two layers:
  * SYNTHETIC unit tests (no data dependency) — prove the ``splice_one`` re-base math, the
    weekend-drop trading-day alignment, the exact boundary anchor, and the truncation/leak property
    deterministically on hand-built frames.
  * REAL-DATA gate tests — run ``splice_verify.run`` over the on-disk 69-name tradfi universe and
    assert every gate: IS bit-identical (max|Δ| == 0.0), iter-016 IS metrics unchanged & ==
    confirmed +0.729/+0.582/+0.875, no weekend bars, clean boundary, past-only leak self-check.
    Skipped (not failed) when the tradfi data is not present in the checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_TRADFI = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
if str(_TRADFI) not in sys.path:
    sys.path.insert(0, str(_TRADFI))

import splice_loader as sl  # noqa: E402
import splice_verify as sv  # noqa: E402


# ------------------------------------------------------------------ synthetic (no data) ----------
def _ms(index: pd.DatetimeIndex) -> np.ndarray:
    return index.view("int64") // 1_000_000


def _synthetic():
    """Yahoo = business days (trading-day grid); perp = daily incl. weekends, overlapping tail."""
    ydates = pd.bdate_range("2025-01-06", "2025-03-31")  # ~trading-day grid
    rng = np.random.default_rng(0)
    ylevel = 100.0 * np.cumprod(1 + rng.normal(0, 0.01, len(ydates)))
    yahoo = pd.DataFrame(
        {
            "open": ylevel * 0.999,
            "high": ylevel * 1.01,
            "low": ylevel * 0.99,
            "close": ylevel,
            "volume": (rng.integers(1_000, 9_000, len(ydates))).astype("int64"),
        },
        index=_ms(ydates),
    )
    pdates = pd.date_range("2025-02-03", "2025-03-31")  # 24/7 incl weekends
    plevel = 250.0 * np.cumprod(1 + rng.normal(0, 0.012, len(pdates)))  # DIFFERENT level (basis)
    perp = pd.DataFrame(
        {
            "open": plevel * 0.998,
            "high": plevel * 1.012,
            "low": plevel * 0.988,
            "close": plevel,
            "volume": (rng.normal(5e4, 1e4, len(pdates))).astype(float),
        },
        index=_ms(pdates),
    )
    return yahoo, perp


def test_synthetic_pre_boundary_bit_identical():
    yahoo, perp = _synthetic()
    spliced, d = sl.splice_one(yahoo, perp)
    assert d is not None
    pre = spliced.index < d
    assert pre.any()
    for field in ("open", "high", "low", "close"):
        assert (spliced.loc[pre, field] == yahoo.loc[pre, field]).all()


def test_synthetic_no_weekend_bars_after_splice():
    yahoo, perp = _synthetic()
    spliced, _ = sl.splice_one(yahoo, perp)
    # output rides the Yahoo trading-day index — weekend perp bars are dropped, none introduced
    assert list(spliced.index) == list(yahoo.index)
    dow = pd.to_datetime(spliced.index, unit="ms").dayofweek
    assert (dow < 5).all()


def test_synthetic_boundary_anchor_exact_and_perp_return():
    yahoo, perp = _synthetic()
    spliced, d = sl.splice_one(yahoo, perp)
    aligned = perp.loc[perp.index.intersection(yahoo.index)].sort_index()
    d1 = int(aligned.index[1])
    # anchor exact at d
    assert spliced.at[d, "close"] == yahoo.at[d, "close"]
    # first spliced return at d+1 is a PURE perp return (Yahoo level cancels)
    perp_ratio = aligned.at[d1, "close"] / aligned.at[d, "close"]
    spliced_ret = spliced.at[d1, "close"] / spliced.at[d, "close"]
    assert abs(spliced_ret - perp_ratio) < 1e-12
    # post-boundary levels are the perp re-based (proportional), not the Yahoo level
    assert abs(spliced.at[d1, "close"] - yahoo.at[d1, "close"]) > 1e-6


def test_synthetic_truncation_is_past_only():
    yahoo, perp = _synthetic()
    full, d = sl.splice_one(yahoo, perp)
    cut = int(full.index[full.index >= d][3])  # a few bars into the perp window
    yt, pt = yahoo[yahoo.index <= cut], perp[perp.index <= cut]
    trunc, _ = sl.splice_one(yt, pt)
    common = trunc.index[trunc.index <= cut]
    for field in ("open", "high", "low", "close"):
        assert (trunc.loc[common, field].to_numpy() == full.loc[common, field].to_numpy()).all()


def test_synthetic_no_perp_returns_pure_yahoo():
    yahoo, _ = _synthetic()
    spliced, d = sl.splice_one(yahoo, None)
    assert d is None
    assert (spliced == yahoo).all().all()


# ------------------------------------------------------------------ real-data gate ----------------
@pytest.fixture(scope="module")
def gate():
    if not sv._universe(None):
        pytest.skip("tradfi data/ not present in this checkout")
    return sv.run()


def test_real_is_bit_identical(gate):
    assert gate["max_dclose"] == 0.0
    assert gate["max_dret"] == 0.0
    assert gate["is_bit_identical"]
    assert gate["earliest_d_after_oos"]  # entire IS window is < perp inception


def test_real_is_metrics_unchanged(gate):
    my, ms = gate["m_y"], gate["m_s"]
    confirmed = sv.CONFIRMED
    for k in confirmed:
        assert ms[k] == my[k]  # spliced == pure-Yahoo, bit-for-bit
        assert abs(ms[k] - confirmed[k]) < 5e-4  # == confirmed +0.729/+0.582/+0.875
    assert gate["is_metrics_match"]


def test_real_no_weekend_bars(gate):
    assert gate["no_weekend"]


def test_real_boundary_clean(gate):
    assert gate["max_anchor"] == 0.0
    assert gate["max_ret_dev"] < 1e-9
    assert gate["boundary_clean"]


def test_real_leak_safe(gate):
    assert gate["max_leak"] == 0.0
    assert gate["leak_safe"]
