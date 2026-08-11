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


# ---------------------------------------------------- mid-series split detection (synthetic) -----
def _inject_split(perp: pd.DataFrame, split_t: int, ratio: float, *, intrabar: bool) -> pd.DataFrame:
    """Un-adjusted split from ``split_t`` onward (perp keeps trading at the OLD share count).

    ``intrabar=True`` mimics the real CRWD case: the split day's own bar straddles the
    transition (open/high still pre-split, low/close already post-split) — the harder case the
    fix must also handle, not just a clean cut starting exactly at the boundary.
    """
    out = perp.copy()
    after = out.index > split_t
    for field in ("open", "high", "low", "close"):
        out.loc[after, field] = out.loc[after, field] / ratio
    if intrabar:
        out.at[split_t, "low"] = out.at[split_t, "low"] / ratio
        out.at[split_t, "close"] = out.at[split_t, "close"] / ratio
        # open/high stay at the PRE-split scale for the split day's own bar
    else:
        for field in ("open", "high", "low", "close"):
            out.at[split_t, field] = out.at[split_t, field] / ratio
    return out


def test_synthetic_mid_series_split_detected_and_corrected():
    yahoo, perp = _synthetic()
    common = sorted(perp.index.intersection(yahoo.index))
    split_t = common[20]  # well clear of both edges given SPLIT_CONFIRM_WINDOW=3
    perp_split = _inject_split(perp, split_t, ratio=4.0, intrabar=True)

    spliced, d = sl.splice_one(yahoo, perp_split)
    ret = spliced["close"].pct_change()
    # the split day itself must NOT read as a ~-75% crash
    assert abs(ret.loc[split_t]) < 0.10
    # OHLC ordering holds even on the contaminated split-day bar and right after it
    idx = spliced.index[(spliced.index >= common[18]) & (spliced.index <= common[23])]
    seg = spliced.loc[idx]
    assert (seg["low"] <= seg[["open", "close"]].min(axis=1) + 1e-9).all()
    assert (seg["high"] >= seg[["open", "close"]].max(axis=1) - 1e-9).all()
    # the TRUE return across the split (from the un-injected perp) is restored, not the raw 1/4 one
    day_after = common[21]
    true_ret = perp.at[day_after, "close"] / perp.at[split_t, "close"]
    corrected_ret = spliced.at[day_after, "close"] / spliced.at[split_t, "close"]
    assert abs(corrected_ret / true_ret - 1.0) < 0.05


def test_synthetic_transient_blip_not_corrected():
    """A one-day divergence that REVERTS the next day is noise, not a split — leave it alone."""
    yahoo, perp = _synthetic()
    common = sorted(perp.index.intersection(yahoo.index))
    blip_t = common[20]
    perp_blip = perp.copy()
    for field in ("open", "high", "low", "close"):
        perp_blip.at[blip_t, field] = perp_blip.at[blip_t, field] * 1.3  # one-day spike, no persist

    plain, _ = sl.splice_one(yahoo, perp)
    blipped, _ = sl.splice_one(yahoo, perp_blip)
    # nothing past the blip day should differ — no split was confirmed, no re-base introduced
    after = blipped.index > blip_t
    for field in ("open", "high", "low", "close"):
        assert (blipped.loc[after, field].to_numpy() == plain.loc[after, field].to_numpy()).all()


def test_detect_split_points_ignores_short_series():
    yahoo, perp = _synthetic()
    common = sorted(perp.index.intersection(yahoo.index))
    aligned = perp.loc[common[:4]].sort_index()  # shorter than 2*window+1
    assert sl._detect_split_points(yahoo, aligned) == []


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
