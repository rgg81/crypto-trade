"""PARITY GUARANTEE — the live portfolio strategy module reproduces the validated backtest exactly.

The live executor computes target weights via crypto_trade.portfolio.strategy, which calls the SAME
backtest code (analysis/portfolio/iter_020). Asserts the deployed position-weight book reproduces
iter_020.banded_net (baseline-v2, SNAP delta=0.010) to machine precision. Slow (loads real klines);
skipped when local data is absent.
"""

import glob
import sys

import numpy as np
import pytest

sys.path.insert(0, "src")


def _have_data() -> bool:
    return len(glob.glob("data/*USDT/8h.csv")) > 50


@pytest.mark.skipif(not _have_data(), reason="needs local kline data (data/<SYM>/8h.csv)")
def test_strategy_reproduces_iter020_baseline_v2():
    from crypto_trade.portfolio import strategy

    sys.path.insert(0, "analysis/portfolio")
    import iter_020_hysteresis as hy

    coins = strategy.load_universe()
    book = hy.canonical_book(coins, hy.build_books(coins))
    ref = hy.banded_net(book, strategy.DELTA, strategy.MODE)          # iter_020 reference net

    pos = strategy.position_weight_book(coins)                        # strategy deployed weights
    scale = book["scale"]
    w = pos.div(scale.replace(0, np.nan), axis=0).fillna(0.0)         # recover pre-scale weights
    pnl = (w * book["ret_fwd"]).sum(axis=1)
    fpnl = -(w * book["fund_next"]).sum(axis=1)
    cost = hy.base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    recon = (pnl + fpnl - cost).dropna()
    recon = (recon * scale.reindex(recon.index)).dropna()

    a, b = ref.align(recon, join="inner")
    assert len(a) > 1000
    assert float((a - b).abs().max()) < 1e-9


@pytest.mark.skipif(not _have_data(), reason="needs local kline data (data/<SYM>/8h.csv)")
def test_next_target_weights_is_sane():
    from crypto_trade.portfolio import strategy

    coins = strategy.load_universe()
    nt = strategy.next_target_weights(coins)
    meta = nt.pop("_meta")
    assert 5 <= len(nt) <= 60                  # ~top-20 plus banded holds outside current top-20
    assert 0.0 < meta["gross"] <= 3.0          # gross within the vol-target max-lev ceiling
    assert all(abs(v) < 1.0 for v in nt.values())
