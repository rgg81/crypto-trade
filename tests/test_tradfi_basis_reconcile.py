"""Tests for the tradfi perp basis/funding reconcile (Task A/B/C helpers).

Pure-unit: synthetic panels/funding — no network, no on-disk data. Guards the load-bearing pieces:
the funding SIGN convention (-w*f), the holding-window funding binning, the resolution-robust ms
edges, the open-to-open forward return, and the book-level basis isolation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_TF = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
if str(_TF) not in sys.path:
    sys.path.insert(0, str(_TF))

import perp_map_tradfi as pm  # noqa: E402
import reconcile_basis_tradfi as rc  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DAY_MS = 86_400_000


def _mid(day: str) -> pd.Timestamp:
    return pd.Timestamp(day)


# ------------------------------------------------------------------ Task A: perp map -------------
def test_static_snapshot_covers_full_universe():
    assert set(pm.PERP_SYMBOL_MAP) == set(ut.SECTOR_MAP)
    assert all(v.endswith("USDT") for v in pm.PERP_SYMBOL_MAP.values())


def test_resolve_matches_symbol_then_base_and_reports_unmapped():
    # AAPLUSDT via exact symbol; BRKBUSDT via stem(BRKB)==baseAsset; a fake key stays unmapped.
    contracts = {
        "AAPLUSDT": {"symbol": "AAPLUSDT", "baseAsset": "AAPL"},
        "BRKBUSDT": {"symbol": "BRKBUSDT", "baseAsset": "BRKB"},
    }
    saved = dict(ut.SECTOR_MAP)
    try:
        ut.SECTOR_MAP.clear()
        ut.SECTOR_MAP.update({"AAPLUSDT": "Tech", "BRKBUSDT": "Fin", "ZZZUSDT": "Tech"})
        mapping, unmapped = pm.resolve_perp_map(contracts)
        assert mapping == {"AAPLUSDT": "AAPLUSDT", "BRKBUSDT": "BRKBUSDT"}
        assert unmapped == ["ZZZUSDT"]
    finally:
        ut.SECTOR_MAP.clear()
        ut.SECTOR_MAP.update(saved)


def test_perp_symbol_map_offline_returns_static():
    assert pm.perp_symbol_map(live=False) == pm.PERP_SYMBOL_MAP


# ------------------------------------------------------------------ Task C: helpers --------------
def test_index_ms_is_resolution_robust():
    # pandas 2.x yields datetime64[ms]; _index_ms must still return true ms epoch.
    ms = [1_769_472_000_000, 1_769_558_400_000]  # two consecutive UTC-midnight days
    idx = pd.to_datetime(ms, unit="ms")
    assert rc._index_ms(idx).tolist() == ms


def test_fwd_ret_is_open_to_open():
    idx = pd.to_datetime([0, DAY_MS, 2 * DAY_MS], unit="ms")
    opens = pd.DataFrame({"A": [10.0, 11.0, 12.0]}, index=idx)
    rf = rc.fwd_ret(opens)
    assert rf["A"].iloc[0] == 11.0 / 10.0 - 1.0
    assert rf["A"].iloc[1] == 12.0 / 11.0 - 1.0
    assert np.isnan(rf["A"].iloc[2])  # last bar has no forward open


def test_daily_funding_bins_holding_window_and_weekend(tmp_path, monkeypatch):
    # panel index = Fri, Mon (weekend skipped). Funding at Fri 00:00/08:00 and Sat 00:00 (weekend)
    # must ALL land in the Fri bin [Fri, Mon); Mon is the last bar -> no upper edge -> excluded.
    fri = int(_mid("2026-01-30").value // 1_000_000)
    mon = int(_mid("2026-02-02").value // 1_000_000)
    idx = pd.to_datetime([fri, mon], unit="ms")
    fdir = tmp_path / "funding_rates"
    fdir.mkdir()
    rows = pd.DataFrame(
        {
            "funding_time": [
                fri,
                fri + 8 * 3600_000,
                fri + DAY_MS,
            ],  # Fri 00:00, Fri 08:00, Sat 00:00
            "funding_rate": [0.001, 0.002, 0.004],
        }
    )
    rows.to_csv(fdir / "XUSDT.csv", index=False)
    out = rc.daily_funding({"XKEY": "XUSDT"}, idx, funding_dir=fdir)
    assert abs(out.loc[idx[0], "XKEY"] - (0.001 + 0.002 + 0.004)) < 1e-12  # weekend swept into Fri
    assert out.loc[idx[1], "XKEY"] == 0.0  # last bar excluded


def test_per_name_funding_sign_long_pays_positive_funding():
    # perp_ret == yahoo_ret; positive funding => long realized < yahoo (long PAYS), gap negative.
    idx = pd.to_datetime([0, DAY_MS, 2 * DAY_MS, 3 * DAY_MS], unit="ms")
    r = pd.Series([0.01, -0.02, 0.03, np.nan], index=idx)
    perp_rf = pd.DataFrame({"A": r})
    yahoo_rf = pd.DataFrame({"A": r})
    fdaily = pd.DataFrame({"A": pd.Series([0.001, 0.001, 0.001, 0.001], index=idx)})
    df = rc.per_name_tracking(perp_rf, yahoo_rf, fdaily)
    assert df.loc["A", "fund_ann_%"] > 0  # longs pay
    assert df.loc["A", "gap_fund_bps"] < df.loc["A", "gap_raw_bps"]  # funding drags realized down
    assert abs(df.loc["A", "gap_raw_bps"]) < 1e-6  # raw perp==yahoo -> zero raw gap


def test_funding_drag_sign_long_cost_short_credit():
    idx = pd.to_datetime([0, DAY_MS], unit="ms")
    perp_rf = pd.DataFrame({"L": [0.0, np.nan], "S": [0.0, np.nan]}, index=idx)
    dep = pd.DataFrame({"L": [0.5, 0.5], "S": [-0.5, -0.5]}, index=idx)  # long L, short S
    fdaily = pd.DataFrame({"L": [0.001, 0.001], "S": [0.001, 0.001]}, index=idx)  # f>0
    d = rc.funding_drag(dep, perp_rf, fdaily)
    assert d["long_leg_ann_%"] < 0  # long pays when f>0 -> cost
    assert d["short_leg_ann_%"] > 0  # short earns when f>0 -> credit
    assert abs(d["net_ann_%"] - (d["long_leg_ann_%"] + d["short_leg_ann_%"])) < 1e-9


def test_book_level_zero_basis_zero_funding_gives_zero_gap():
    idx = pd.to_datetime([i * DAY_MS for i in range(5)], unit="ms")
    rets = pd.Series([0.01, -0.02, 0.015, 0.0, np.nan], index=idx)
    perp_rf = pd.DataFrame({"A": rets, "B": rets})
    yahoo_rf = perp_rf.copy()  # identical -> zero basis
    fdaily = pd.DataFrame({"A": [0.0] * 5, "B": [0.0] * 5}, index=idx)  # no funding
    dep = pd.DataFrame({"A": [0.3] * 5, "B": [-0.2] * 5}, index=idx)
    bt = pd.Series([0.0] * 5, index=idx)
    b = rc.book_level(dep, perp_rf, yahoo_rf, fdaily, bt)
    assert abs(b["cum_gap_bps"]) < 1e-6
    assert abs(b["te_daily_ann_%"]) < 1e-9
