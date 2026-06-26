"""Bit-exact live-parity tests for the metals paper engine (POSITION-LEVEL champion).

The live engine deploys `desk_book.iloc[-1]` and books `desk_net`. Both come from the SAME `desk`
matrix, so parity is structural. These prove it:
  1. `deployed_from_raw` net == `net_from_raw` net (the leg decomposition is faithful per leg);
  2. the live target == the last row of the deployed desk book (orders match the book);
  3. `regime_net` == the net recomputed FROM the deployed book (PnL is the positions' PnL);
  4. the desk net is LEAK-FREE (corrupting the future leaves the past net bit-identical);
  5. the breadth-acceleration signal is leak-free.
All synthetic; a real-data check skips if metals aren't ingested.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_METALS = _ROOT / "analysis" / "portfolio" / "metals"
sys.path.insert(0, str(_METALS))

import iter_008_allweather as a8  # noqa: E402
import iter_010_breadth_accel as i10  # noqa: E402
import live_weights as lw  # noqa: E402
import universe_metals as um  # noqa: E402


def _make_coins(n: int = 950, seed: int = 0) -> dict[str, pd.DataFrame]:
    """Synthetic 4-metal OHLCV (real tickers, gold first) with enough candles for SMA(450)."""
    rng = np.random.default_rng(seed)
    start = int(pd.Timestamp("2018-01-01").value // 1_000_000)
    ot = start + np.arange(n) * (8 * 3600 * 1000)
    coins: dict[str, pd.DataFrame] = {}
    for _i, tk in enumerate(um.UNIVERSE):
        close = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.013, n)))
        opn = np.concatenate([[close[0]], close[:-1]])
        coins[tk] = pd.DataFrame(
            {
                "open": opn,
                "high": np.maximum(opn, close) * 1.001,
                "low": np.minimum(opn, close) * 0.999,
                "close": close,
                "volume": 1.0,
            },
            index=pd.Index(ot, name="open_time"),
        )
    return coins


def _corrupt_future(coins: dict[str, pd.DataFrame], cut_ms: int) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s, d in coins.items():
        d = d.copy()
        m = d.index >= cut_ms
        for col in ("open", "high", "low", "close"):
            d.loc[m, col] = d.loc[m, col].to_numpy() * 2.5 + 11.0
        out[s] = d
    return out


def test_deployed_from_raw_net_matches_net_from_raw():
    """The deployed decomposition returns the SAME net as the canonical core (no drift)."""
    coins = _make_coins(seed=1)
    pan = um.panels(coins)
    raw = a8._anchor_flatbear_raw(coins, "ma", 450, 0.6, 0)[0]
    net_ref, _ = um.net_from_raw(raw, pan["ret_fwd"])
    net_dep, _ = um.deployed_from_raw(raw, pan["ret_fwd"])
    pd.testing.assert_series_equal(net_ref, net_dep)


def test_target_weights_are_last_row_of_book():
    """next_target_weights_metals == the last row of the deployed desk book (non-trivial)."""
    coins = _make_coins(seed=3)
    desk, _ = lw.deployed_weight_book(coins)
    tgt = lw.next_target_weights_metals(coins)
    last = desk.iloc[-1]
    for s, v in last[last.abs() > 1e-9].items():
        assert s in tgt and abs(tgt[s] - float(v)) < 1e-12
    assert tgt["_meta"]["n_positions"] == int((last.abs() > 1e-9).sum())


def test_net_is_the_positions_pnl():
    """regime_net == net recomputed FROM the deployed book — the PnL IS the positions' PnL."""
    coins = _make_coins(seed=2)
    desk, _ = lw.deployed_weight_book(coins)
    rf = um.panels(coins)["ret_fwd"]
    recon = (
        (desk * rf.reindex(columns=desk.columns)).sum(axis=1)
        - um.COST_SIDE * desk.diff().abs().sum(axis=1)
    ).dropna()
    net = lw.regime_net(coins)
    common = net.index.intersection(recon.index)
    pd.testing.assert_series_equal(net.loc[common], recon.loc[common], check_names=False)


def test_desk_net_is_leak_free():
    """Corrupting every OHLC at/after a cutoff must leave the past desk net bit-identical.

    Boundary: ret_fwd[t]=open[t+1]/open[t] means corrupting bars >= cut can legitimately move
    net[cut-1] (it realises into open[cut]); assert bars strictly before cut-1 are bit-identical.
    """
    coins = _make_coins(seed=4)
    idx = next(iter(coins.values())).index
    cut = int(idx[len(idx) - 200])
    n0 = lw.regime_net(coins)
    n1 = lw.regime_net(_corrupt_future(coins, cut))
    bound = pd.Timestamp(int(idx[len(idx) - 201]), unit="ms")
    common = n0.index.intersection(n1.index)
    common = common[common < bound]
    assert len(common) > 100
    pd.testing.assert_series_equal(n0.loc[common], n1.loc[common])


def test_breadth_accel_signal_is_leak_free():
    """The breadth-acceleration signal must not change in the past when the future is corrupted."""
    coins = _make_coins(seed=5)
    close0 = um.panels(coins)["close"]
    cut_ms = int(next(iter(coins.values())).index[600])
    s0 = i10.breadth_accel(close0, 42, 252, 450)
    close1 = um.panels(_corrupt_future(coins, cut_ms))["close"]
    s1 = i10.breadth_accel(close1, 42, 252, 450)
    bound = s0.index[599]
    common = s0.index.intersection(s1.index)
    common = common[common <= bound]
    pd.testing.assert_series_equal(s0.loc[common], s1.loc[common])


def test_dispersion_leg_is_dollar_neutral():
    """The dispersion sleeve's deployed positions sum to ~0 each bar (bear-payer is $-neutral)."""
    coins = _make_coins(seed=6)
    _, dep_d = um.deployed_from_raw(
        __import__("iter_002_mn_overlay").mn_dispersion_raw(um.panels(coins)["close"]),
        um.panels(coins)["ret_fwd"],
    )
    active = dep_d[dep_d.abs().sum(axis=1) > 1e-9]
    assert active.sum(axis=1).abs().max() < 1e-9


@pytest.mark.parametrize("_", [0])
def test_real_data_target_weights_sane(_):
    """On the real ingested metals, the live target is finite and the net is the positions' PnL."""
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        pytest.skip("metals data not ingested")
    coins = um.load_metals()
    tgt = lw.next_target_weights_metals(coins)
    assert tgt["_meta"]["gross"] >= 0.0 and np.isfinite(tgt["_meta"]["gross"])
    desk, _ = lw.deployed_weight_book(coins)
    rf = um.panels(coins)["ret_fwd"]
    recon = (
        (desk * rf.reindex(columns=desk.columns)).sum(axis=1)
        - um.COST_SIDE * desk.diff().abs().sum(axis=1)
    ).dropna()
    net = lw.regime_net(coins)
    common = net.index.intersection(recon.index)
    assert float((net.loc[common] - recon.loc[common]).abs().max()) < 1e-12
