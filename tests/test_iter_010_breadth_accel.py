"""Tests for iter-010 — breadth-ACCELERATION gate + POSITION-LEVEL honest net (the champion).

  * the breadth-acceleration signal is a real mechanism (differs from the breadth level);
  * position-level desk_net charges cost on the desk's TRUE turnover (more than a no-cost sum);
  * on real metals the champion is all-3-Sharpe-positive AND its accel gate beats the iter-009
    level gate on the bear (the iter-010 claim), under identical honest accounting.
Synthetic where possible; the scorecard claim skips if the metals CSVs aren't ingested.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "analysis" / "portfolio" / "metals"))

import iter_008_allweather as a8  # noqa: E402
import iter_010_breadth_accel as i10  # noqa: E402
import universe_metals as um  # noqa: E402


def _make_coins(n: int = 950, seed: int = 0) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    ot = int(pd.Timestamp("2018-01-01").value // 1_000_000) + np.arange(n) * (8 * 3600 * 1000)
    coins: dict[str, pd.DataFrame] = {}
    for tk in um.UNIVERSE:
        close = 100 * np.exp(np.cumsum(rng.normal(-0.0002, 0.013, n)))
        opn = np.concatenate([[close[0]], close[:-1]])
        coins[tk] = pd.DataFrame(
            {"open": opn, "high": np.maximum(opn, close) * 1.001,
             "low": np.minimum(opn, close) * 0.999, "close": close, "volume": 1.0},
            index=pd.Index(ot, name="open_time"),
        )
    return coins


def test_breadth_accel_differs_from_level():
    """The acceleration signal is genuinely distinct from the breadth level (a real mechanism)."""
    close = um.panels(_make_coins(seed=2))["close"]
    accel = i10.breadth_accel(close, 42, 252, 450)
    level = a8.breadth_down(close, "ma", 450)
    common = accel.dropna().index.intersection(level.index)
    assert not np.allclose(accel.loc[common].to_numpy(), level.loc[common].to_numpy())


def test_position_level_net_charges_true_turnover():
    """desk_net subtracts cost on the desk's actual |Δposition| (strictly below the gross PnL)."""
    coins = _make_coins(seed=3)
    desk, _ = i10.desk_book(coins)
    rf = um.panels(coins)["ret_fwd"]
    gross_pnl = (desk * rf.reindex(columns=desk.columns)).sum(axis=1).dropna()
    net = i10.desk_net(coins)
    common = net.index.intersection(gross_pnl.index)
    # net = gross_pnl - cost, and the desk genuinely turns over -> total net < total gross
    assert net.loc[common].sum() < gross_pnl.loc[common].sum()


def test_champion_all_weather_and_beats_level_gate_on_bear():
    """Real metals: iter-010 champion is all-3-positive AND its accel gate beats the iter-009 level
    gate (w_blend=0) on the bear, under identical position-level accounting."""
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        import pytest

        pytest.skip("metals data not ingested")
    a8.bear.ingest_bear()
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)

    def regimes(**over):
        nb, nm = i10.desk_net(cb, **over), i10.desk_net(cm, **over)
        return (
            i10._seg(nb, "2011-09-01", "2015-03-24")["sharpe"],
            i10._seg(nm, "2000-01-01", "2025-03-24")["sharpe"],
            i10._seg(nm, "2025-03-24", "2100-01-01")["sharpe"],
        )

    b_acc, is_acc, u_acc = regimes()  # iter-010 champion (w_blend=0.65)
    b_lvl, _, _ = regimes(w_blend=0.0)  # iter-009 level gate
    assert b_acc > 0 and is_acc > 0 and u_acc > 0  # all-weather
    assert b_acc > b_lvl + 0.05  # the acceleration gate materially beats the level gate on the bear
