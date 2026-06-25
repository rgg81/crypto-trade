"""Bit-exact live-parity tests for the metals paper engine's weight extraction.

The live engine must deploy positions BIT-IDENTICAL to the backtest. These prove the deployed-weight
reconstruction (`live_weights`) reproduces the backtest book exactly:
  1. `deployed_from_raw` net == `net_from_raw` net (the decomposition is faithful per leg).
  2. the two legs recombined == `regime_book` net (the live legs ARE the backtest book).
  3. `next_target_weights_metals` is consistent with the full deployed book + the dollar-neutral /
     long-only invariants of each sleeve hold in the deployed positions.
All synthetic (no data load); a real-data check skips if metals aren't ingested.
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

import iter_008_allweather as r8  # noqa: E402
import live_weights as lw  # noqa: E402
import universe_metals as um  # noqa: E402


def _make_coins(n: int = 950, seed: int = 0) -> dict[str, pd.DataFrame]:
    """Synthetic 4-metal OHLCV (real tickers, gold first) with enough candles for SMA(450)."""
    rng = np.random.default_rng(seed)
    start = int(pd.Timestamp("2018-01-01").value // 1_000_000)
    ot = start + np.arange(n) * (8 * 3600 * 1000)
    coins: dict[str, pd.DataFrame] = {}
    for i, tk in enumerate(um.UNIVERSE):
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


def test_deployed_from_raw_net_matches_net_from_raw():
    """The deployed decomposition returns the SAME net as the canonical core (no drift)."""
    coins = _make_coins(seed=1)
    pan = um.panels(coins)
    raw = r8._anchor_flatbear_raw(coins, "ma", r8.CHAMP["win"], r8.CHAMP["thresh"], 0)[0]
    net_ref, _ = um.net_from_raw(raw, pan["ret_fwd"])
    net_dep, _ = um.deployed_from_raw(raw, pan["ret_fwd"])
    pd.testing.assert_series_equal(net_ref, net_dep)


def test_live_legs_recombine_to_regime_book_net():
    """The live-extracted legs (a_w·net_anchor_braked + d_w·net_disp) == regime_book net, bit-exact.

    This is THE parity guarantee: the positions the live engine deploys ARE the backtest book.
    """
    coins = _make_coins(seed=2)
    net_book, _ = r8.regime_book(coins)
    _, net_a_braked, _, net_d, d_w, _ = lw._legs_deployed(coins)
    recon = r8.CHAMP["a_w"] * net_a_braked + d_w * net_d
    common = net_book.index.intersection(recon.index)
    pd.testing.assert_series_equal(net_book.loc[common], recon.loc[common], check_names=False)


def test_target_weights_consistent_with_deployed_book():
    """next_target_weights_metals == the last row of the deployed book (non-trivial entries)."""
    coins = _make_coins(seed=3)
    desk, _ = lw.deployed_weight_book(coins)
    tgt = lw.next_target_weights_metals(coins)
    last = desk.iloc[-1]
    for s, v in last[last.abs() > 1e-9].items():
        assert s in tgt and abs(tgt[s] - float(v)) < 1e-12
    assert tgt["_meta"]["n_positions"] == int((last.abs() > 1e-9).sum())


def test_dispersion_leg_is_dollar_neutral_in_deployed_book():
    """The dispersion sleeve's deployed positions sum to ~0 each bar (bear-payer is $-neutral)."""
    coins = _make_coins(seed=4)
    _, _, dep_d, _, _, _ = lw._legs_deployed(coins)
    active = dep_d[dep_d.abs().sum(axis=1) > 1e-9]
    assert active.sum(axis=1).abs().max() < 1e-9


def test_anchor_sleeve_is_long_only_in_deployed_book():
    """The anchor sleeve never shorts: every braked anchor deployed weight is >= 0."""
    coins = _make_coins(seed=5)
    dep_a_braked = lw._legs_deployed(coins)[0]
    assert (dep_a_braked.fillna(0.0) >= -1e-12).all().all()


@pytest.mark.parametrize("_", [0])
def test_real_data_target_weights_sane(_):
    """On the real ingested metals, the live target is finite and matches the deployed book."""
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        pytest.skip("metals data not ingested")
    coins = um.load_metals()
    tgt = lw.next_target_weights_metals(coins)
    assert tgt["_meta"]["gross"] >= 0.0 and np.isfinite(tgt["_meta"]["gross"])
    # the live legs still recombine to the book on REAL data (the deployment is parity-exact)
    net_book, _ = r8.regime_book(coins)
    _, net_a_braked, _, net_d, d_w, _ = lw._legs_deployed(coins)
    recon = r8.CHAMP["a_w"] * net_a_braked + d_w * net_d
    common = net_book.index.intersection(recon.index)
    assert float((net_book.loc[common] - recon.loc[common]).abs().max()) < 1e-12
