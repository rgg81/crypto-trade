"""team-10 strategy tests — t10-ts-trend-v1.

Self-contained: synthetic panels built with numpy/pandas ONLY, plus the team-local
``strategy`` module. NO import of pytest / the evaluator / any data path — so this file
passes the static-scan import whitelist (the harness scans every .py in the team dir).
pytest collects the bare ``test_*`` functions without needing to be imported.

Covered:
- determinism: two calls on identical inputs -> bit-identical weights.
- future-bar corruption (the mandatory leak self-check): mangle every bar STRICTLY AFTER a
  cut (close *7 + 5, the harness's transform); weights at/before the cut must be unchanged.
- truncated replay: run on data truncated at a cut; weights <= cut must be unchanged.
- same-bar: perturb close[t*] only; weights STRICTLY BEFORE t* must be unchanged.
- interface sanity: output aligns to close's index/columns, is finite, and ``aux`` is
  genuinely unused (weights identical under a scrambled aux).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy


def _make_panels(n_days: int = 640, n_tickers: int = 9, seed: int = 12345):
    """Synthetic OHLCV panels (dates x tickers) via per-name geometric random walks, with
    one ragged (late-starting) name to exercise NaN handling. Only ``close`` is consumed."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n_days)
    tickers = [f"SYM{i:02d}USDT" for i in range(n_tickers)]
    rets = rng.normal(0.0004, 0.02, size=(n_days, n_tickers))
    close = pd.DataFrame(100.0 * np.exp(np.cumsum(rets, axis=0)), index=idx, columns=tickers)
    # ragged start: last ticker only comes alive after row 300 (NaN before)
    close.iloc[:300, -1] = np.nan
    pn = {
        "open": close.shift(1).fillna(close),
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": pd.DataFrame(
            rng.uniform(1e5, 1e6, size=(n_days, n_tickers)), index=idx, columns=tickers
        ),
    }
    aux = {"vix": None, "sector_map": {t: "X" for t in tickers}, "seed": 20260717}
    return pn, aux


def _corrupt_after(pn: dict, cut) -> dict:
    """Mangle every bar STRICTLY AFTER ``cut`` (harness transform: price *7 + 5)."""
    out = {k: v.copy() for k, v in pn.items()}
    mask = out["close"].index > cut
    for k in ("open", "high", "low", "close"):
        out[k].loc[mask] = out[k].loc[mask] * 7.0 + 5.0
    out["volume"].loc[mask] = out["volume"].loc[mask] * 3.0 + 1.0
    return out


def _truncate(pn: dict, cut) -> dict:
    return {k: v[v.index <= cut].copy() for k, v in pn.items()}


def test_determinism():
    pn, aux = _make_panels()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_interface_shape_and_finite():
    pn, aux = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    assert list(w.index) == list(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)
    # EMA of fillna(0) with min_periods=1 => every cell defined, nothing infinite
    assert np.isfinite(w.to_numpy()).all()


def test_aux_is_unused():
    """The strategy must not consume aux (no seed/vix/sector dependence)."""
    pn, aux = _make_panels()
    w_base = strategy.build_raw_weights(pn, aux)
    scrambled = {"vix": None, "sector_map": {}, "seed": 999999}
    w_scrambled = strategy.build_raw_weights(pn, scrambled)
    pd.testing.assert_frame_equal(w_base, w_scrambled, check_exact=True)


def test_future_corruption_leak_selfcheck():
    """Mangle every bar strictly after each cut; weights at/before the cut must be identical."""
    pn, aux = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)
    idx = pn["close"].index
    for frac in (0.45, 0.6, 0.8):
        cut = idx[int(len(idx) * frac)]
        w_c = strategy.build_raw_weights(_corrupt_after(pn, cut), aux)
        pd.testing.assert_frame_equal(
            w_full[w_full.index <= cut], w_c[w_c.index <= cut], check_exact=True
        )


def test_truncated_replay():
    """Weights on rows <= cut must be identical whether or not future rows exist at all."""
    pn, aux = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)
    idx = pn["close"].index
    for frac in (0.5, 0.7, 0.95):
        cut = idx[int(len(idx) * frac)]
        w_t = strategy.build_raw_weights(_truncate(pn, cut), aux)
        pd.testing.assert_frame_equal(
            w_full[w_full.index <= cut], w_t[w_t.index <= cut], check_exact=True
        )


def test_same_bar_perturbation():
    """Perturb close[t*] only; weights STRICTLY BEFORE t* must be unchanged."""
    pn, aux = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)
    idx = pn["close"].index
    t_star = idx[int(len(idx) * 0.7)]
    pn_p = {k: v.copy() for k, v in pn.items()}
    pn_p["close"].loc[t_star] = pn_p["close"].loc[t_star] * 1.001
    w_p = strategy.build_raw_weights(pn_p, aux)
    pd.testing.assert_frame_equal(
        w_full[w_full.index < t_star], w_p[w_p.index < t_star], check_exact=True
    )
