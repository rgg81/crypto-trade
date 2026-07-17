"""team-05 strategy tests — Amihud illiquidity rank book.

Self-contained: imports are limited to numpy, pandas, and the local ``strategy`` module so
the tournament static scan (which scans every team .py) stays clean — no ``pytest`` import,
no evaluator import, no data access. Tests build synthetic OHLCV panels shaped exactly like
``engine.team_view(pn)`` (dates x tickers DataFrames) and exercise the leak-proofing contract
directly on ``build_raw_weights``.

Mandatory checks:
  * FUTURE CORRUPTION — mangle every bar strictly AFTER a cut; weights at/before the cut must
    be byte-identical (past-only guarantee).
  * DETERMINISM       — two fresh calls on identical inputs emit identical weights.
Plus structural sanity: dollar-neutral centered ranks, breadth, and long-illiquid direction.
"""

import numpy as np
import pandas as pd

import strategy

SEED = 20260717


def _synthetic_panels(n_days=420, n_tickers=10, seed=0, ragged=True):
    """Positive random-walk closes + positive volumes on a business-day grid. Optional ragged
    starts (early NaNs) to mirror the point-in-time universe the strategy must tolerate."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2014-01-01", periods=n_days, freq="B")
    tickers = [f"T{i:02d}USDT" for i in range(n_tickers)]

    steps = rng.normal(0.0, 0.02, size=(n_days, n_tickers))
    close = 100.0 * np.exp(np.cumsum(steps, axis=0))
    volume = rng.uniform(1.0e5, 5.0e7, size=(n_days, n_tickers))

    close_df = pd.DataFrame(close, index=idx, columns=tickers)
    vol_df = pd.DataFrame(volume, index=idx, columns=tickers)

    if ragged:
        # two names IPO late so early rows have <126 valid obs for them
        for j, start in ((n_tickers - 1, 200), (n_tickers - 2, 90)):
            close_df.iloc[:start, j] = np.nan
            vol_df.iloc[:start, j] = np.nan

    pn = {
        "open": close_df.copy(),
        "high": close_df.copy(),
        "low": close_df.copy(),
        "close": close_df.copy(),
        "volume": vol_df.copy(),
    }
    aux = {"vix": None, "sector_map": {t: "X" for t in tickers}, "seed": SEED}
    return pn, aux


def test_determinism():
    pn, aux = _synthetic_panels(seed=1)
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_seed_unused_determinism():
    """Weights must not depend on aux['seed'] — the book carries no randomness."""
    pn, aux = _synthetic_panels(seed=2)
    w_a = strategy.build_raw_weights(pn, {**aux, "seed": 0})
    w_b = strategy.build_raw_weights(pn, {**aux, "seed": 999999})
    pd.testing.assert_frame_equal(w_a, w_b, check_exact=True)


def test_future_corruption_past_only():
    """Mangle every bar strictly AFTER a cut (prices x7+5, volume x3+1) — the harness's own
    recipe — and assert weights at/before the cut are byte-identical."""
    pn, aux = _synthetic_panels(seed=3)
    w_full = strategy.build_raw_weights(pn, aux)

    idx = pn["close"].index
    cut = idx[len(idx) * 2 // 3]

    pn_c = {k: v.copy() for k, v in pn.items()}
    after = pn_c["close"].index > cut
    for k in ("open", "high", "low", "close"):
        pn_c[k].loc[after] = pn_c[k].loc[after] * 7.0 + 5.0
    pn_c["volume"].loc[after] = pn_c["volume"].loc[after] * 3.0 + 1.0

    w_corrupt = strategy.build_raw_weights(pn_c, aux)

    a = w_full[w_full.index <= cut]
    b = w_corrupt[w_corrupt.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_truncation_equivalence():
    """Weights on data truncated at a cut must match the full-panel weights at/before the cut
    (no full-sample statistics, no panel-length-derived state)."""
    pn, aux = _synthetic_panels(seed=4)
    w_full = strategy.build_raw_weights(pn, aux)

    idx = pn["close"].index
    cut = idx[300]
    pn_t = {k: v[v.index <= cut].copy() for k, v in pn.items()}
    w_trunc = strategy.build_raw_weights(pn_t, aux)

    a = w_full[w_full.index <= cut]
    b = w_trunc[w_trunc.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_dollar_neutral_and_breadth():
    """Late rows (full history) produce symmetric centered ranks: eligible weights sum to ~0
    (dollar-neutral pre-caps) with breadth = every eligible name on both sides."""
    pn, aux = _synthetic_panels(seed=5)
    w = strategy.build_raw_weights(pn, aux)

    tail = w.iloc[-1].dropna()
    assert len(tail) >= 8  # all 10 names live by the last row
    assert abs(tail.sum()) < 1e-9  # centered ranks are dollar-neutral
    assert (tail > 0).sum() >= 3 and (tail < 0).sum() >= 3


def test_direction_long_illiquid():
    """A name engineered to be strictly the most illiquid (highest |ret|/dollar every day)
    must receive the largest positive weight; the most liquid the largest negative."""
    n_days, n_tickers = 400, 6
    idx = pd.date_range("2014-01-01", periods=n_days, freq="B")
    tickers = [f"T{i:02d}USDT" for i in range(n_tickers)]
    rng = np.random.default_rng(7)

    # ALL tickers share one close path => identical |ret| every day. Illiquidity then depends
    # only on dollar volume, which we scale monotonically across tickers.
    one_path = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.02, size=n_days)))
    close = pd.DataFrame(np.tile(one_path[:, None], (1, n_tickers)), index=idx, columns=tickers)
    base_vol = rng.uniform(1.0e6, 2.0e6, size=(n_days, 1))
    scale = np.arange(1, n_tickers + 1) * 1.0e3  # T00 tiniest $vol (most illiquid) ... T05 largest
    volume = pd.DataFrame(base_vol * scale, index=idx, columns=tickers)

    pn = {"open": close, "high": close, "low": close, "close": close, "volume": volume}
    aux = {"vix": None, "sector_map": {}, "seed": SEED}
    w = strategy.build_raw_weights(pn, aux).iloc[-1]

    assert w.idxmax() == "T00USDT"  # most illiquid -> most long
    assert w.idxmin() == f"T{n_tickers - 1:02d}USDT"  # most liquid -> most short
