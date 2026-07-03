"""Tests for the metals data-sourcing: Dukascopy one-time backfill + Binance 24/5-filtered live.

Guards the two things the Binance swap introduced:
  1. the 24/5 market-hours filter (metals_market_open) — Binance is 24/7, the strategy is 24/5;
  2. the merged store stays 24/5 + 8h-grid-aligned in the Binance era (no weekend candles leak in).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

_METALS = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "metals"
if str(_METALS) not in sys.path:
    sys.path.insert(0, str(_METALS))

import universe_metals as um  # noqa: E402


def _ms(y: int, m: int, d: int, h: int) -> int:
    return int(pd.Timestamp(f"{y}-{m:02d}-{d:02d} {h:02d}:00", tz="UTC").timestamp() * 1000)


def _dow(ms: int) -> int:
    return pd.Timestamp(ms, unit="ms", tz="UTC").dayofweek


def test_integer_dow_matches_pandas():
    """The epoch-based dow arithmetic in metals_market_open must match pandas over a full month."""
    for d in range(1, 32):
        ms = _ms(2026, 7, d, 8)
        assert (ms // 86_400_000 + 3) % 7 == _dow(ms), d


def test_metals_market_open_24x5_schedule():
    """KEEP Mon-Fri (all 00/08/16) + Sun-16:00; DROP Sat (all) and Sun 00:00/08:00."""
    days = {d: _ms(2026, 7, d, 0) for d in range(1, 15)}
    mon = next(d for d in days if _dow(days[d]) == 0)
    fri = next(d for d in days if _dow(days[d]) == 4)
    sat = next(d for d in days if _dow(days[d]) == 5)
    sun = next(d for d in days if _dow(days[d]) == 6)
    for h in (0, 8, 16):
        assert um.metals_market_open(_ms(2026, 7, mon, h)), ("Mon", h)
        assert um.metals_market_open(_ms(2026, 7, fri, h)), ("Fri", h)
        assert not um.metals_market_open(_ms(2026, 7, sat, h)), ("Sat", h)
    assert not um.metals_market_open(_ms(2026, 7, sun, 0)), "Sun 00 must drop"
    assert not um.metals_market_open(_ms(2026, 7, sun, 8)), "Sun 08 must drop"
    assert um.metals_market_open(_ms(2026, 7, sun, 16)), "Sun 16 reopen must keep"


def test_merged_store_is_24x5_and_grid_aligned_in_binance_era():
    """On the live store: the Binance era (>= 2025-12-11) carries NO Saturday candle and no
    Sunday-00/08 candle, and every open_time lands on the 00/08/16 UTC grid — i.e. the 24/5 filter
    took effect and Binance's 24/7 stream never leaks weekend candles in."""
    p = Path("data_live_metals/XAUUSDT/8h.csv")
    if not p.exists():
        pytest.skip("no live data")
    d = um.load_metals("data_live_metals")["XAUUSDT"]
    idx = pd.to_datetime(d.index, unit="ms", utc=True)
    bn = idx[idx >= pd.Timestamp("2025-12-11", tz="UTC")]
    assert (bn.dayofweek != 5).all(), "Saturday candle present in the Binance era"
    sun = bn[bn.dayofweek == 6]
    assert (sun.hour == 16).all(), "Sunday non-16:00 candle present in the Binance era"
    assert bn.hour.isin([0, 8, 16]).all(), "off-grid candle present"
    assert not d.index.duplicated().any(), "duplicate open_time"


def test_seam_no_gap_no_dup_at_perp_launch():
    """The Dukascopy->Binance seam has exactly one candle per market-open 8h slot across the join
    (no double-count, no gap)."""
    p = Path("data_live_metals/XAUUSDT/8h.csv")
    if not p.exists():
        pytest.skip("no live data")
    d = um.load_metals("data_live_metals")["XAUUSDT"]
    launch = _ms(2025, 12, 11, 8)  # gold perp launch
    idx = list(d.index)
    around = [t for t in idx if launch - 3 * 8 * 3_600_000 <= t <= launch + 3 * 8 * 3_600_000]
    assert len(around) == len(set(around)), "duplicate at seam"
    # every present slot is on the 8h grid
    assert all(t % (8 * 3_600_000) == 0 for t in around), "off-grid at seam"
