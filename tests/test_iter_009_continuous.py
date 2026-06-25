"""Tests for the iter-009 CONTINUOUS-breadth dispersion gate (leak-free bear-edge recovery).

  * the continuous regime weight d_w is LEAK-FREE (corrupting the future leaves past d_w bit-id);
  * the continuous champion is all-3-Sharpe-positive AND its worst-DD is no worse than the L2+brake
    baseline (the iter-009 claim the look-ahead-inflated binary champ failed once de-leaked).
  * gate='continuous' genuinely differs from gate='binary' (it's a real mechanism change).
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
import iter_009_continuous as i9  # noqa: E402
import universe_metals as um  # noqa: E402


def _synth_coins(n: int = 1200, seed: int = 7) -> dict[str, pd.DataFrame]:
    """Synthetic 4-metal OHLCV with a bear→bull arc (mirrors the iter-008 test fixture)."""
    rng = np.random.default_rng(seed)
    t0 = int(pd.Timestamp("2016-01-01").value // 10**6)
    ot = t0 + 8 * 3600 * 1000 * np.arange(n)
    drift = np.concatenate([np.full(n // 2, -0.0006), np.full(n - n // 2, +0.0007)])
    coins: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(um.UNIVERSE):
        close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.012, n) + drift + 0.0002 * i))
        op = close * (1 + rng.normal(0, 0.001, n))
        coins[sym] = pd.DataFrame(
            {
                "open_time": ot,
                "open": op,
                "high": np.maximum(op, close) * 1.002,
                "low": np.minimum(op, close) * 0.998,
                "close": close,
                "volume": rng.uniform(1e3, 1e4, n),
            }
        ).set_index("open_time")
    return coins


def _corrupt_future(coins: dict[str, pd.DataFrame], cut: int) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for sym, df in coins.items():
        d = df.copy()
        for col in ("open", "high", "low", "close"):
            d.iloc[cut:, d.columns.get_loc(col)] = d.iloc[cut:][col].to_numpy() * 3.0 + 17.0
        out[sym] = d
    return out


def test_continuous_regime_weight_is_leak_free():
    """Corrupting every close AT/AFTER a cutoff must not change the continuous d_w BEFORE it.

    This is the exact failure mode the live-parity reconcile caught in the binary gate (d_w[t] using
    b[t]); the continuous gate must be clean — d_w[t] depends only on breadth[t-1] (past-only).
    """
    coins = _synth_coins()
    cut = 800
    _, b = a8.anchor_leg_braked(coins)
    kw = dict(gate="continuous", kind="ma", win=450, dw_bull=0.25, dw_bear=1.0)
    dw0 = a8.regime_dw(coins, b, **kw)
    coins_c = _corrupt_future(coins, cut)
    _, b_c = a8.anchor_leg_braked(coins_c)
    dw1 = a8.regime_dw(coins_c, b_c, **kw)
    bound = dw0.index[cut - 1]  # corruption may touch realisation bar cut-1; assert strictly < it
    common = dw0.index.intersection(dw1.index)
    common = common[common < bound]
    assert len(common) > 100
    pd.testing.assert_series_equal(dw0.loc[common], dw1.loc[common])


def test_continuous_gate_differs_from_binary():
    """gate='continuous' is a real mechanism change — the d_w series is not the binary one."""
    coins = _synth_coins()
    _, b = a8.anchor_leg_braked(coins)
    kw = dict(kind="ma", win=450, dw_bull=0.25, dw_bear=1.0)
    dw_bin = a8.regime_dw(coins, b, gate="binary", **kw)
    dw_con = a8.regime_dw(coins, b, gate="continuous", **kw)
    assert not np.allclose(dw_bin.to_numpy(), dw_con.to_numpy())
    # continuous d_w lives in [dw_bull, dw_bear] and takes intermediate (non-endpoint) values
    inside = dw_con[(dw_con > 0.25 + 1e-6) & (dw_con < 1.0 - 1e-6)]
    assert len(inside) > 50  # genuinely continuous, not a 2-level step


def test_champ9_is_all_three_positive_and_beats_baseline_dd():
    """On real metals: iter-009 continuous champ is all-3-+ AND worst-DD ≤ the L2+brake baseline."""
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        import pytest

        pytest.skip("metals data not ingested")
    rows = i9.scorecard()
    champ = rows["iter-009 CONTINUOUS champ (dW.25->1.0)"]
    base = rows["L2 + brake (baseline)"]
    assert champ["bsr"] > 0 and champ["isr"] > 0 and champ["usr"] > 0 and champ["allp"]
    # the iter-009 claim the binary champ FAILED: the tail is no worse than the simpler baseline
    assert champ["worst"] >= base["worst"] - 1e-9
