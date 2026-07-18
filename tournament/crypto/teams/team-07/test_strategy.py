"""team-07 team tests for the vol-DYNAMICS strategy.

Self-contained: builds synthetic panels with numpy/pandas only and calls the strategy
directly (`import strategy`). No evaluator imports, no file reads, no third-party test deps —
the whole file passes the tournament static import/path scan. pytest discovers the `test_*`
functions without any import of its own. Covers the §7-mandated checks: future-corruption,
determinism, widening, NaN-tolerance, and same-bar convention sanity.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

STEP = "8h"


def _panels(n_rows: int = 400, n_syms: int = 12, seed: int = 7):
    """Deterministic synthetic (pn, aux) on an 8h grid. Only close + eligibility matter to the
    strategy, but a full 9-panel dict is supplied for realism."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n_rows, freq=STEP)
    syms = [f"SYM{i:02d}" for i in range(n_syms)]
    # per-symbol log-return streams with heterogeneous vol so the cross-section is non-trivial
    close = {}
    for i, s in enumerate(syms):
        vol = 0.005 + 0.02 * (i / n_syms)
        rets = rng.normal(0.0, vol, size=n_rows)
        close[s] = 100.0 * np.exp(np.cumsum(rets))
    C = pd.DataFrame(close, index=idx, columns=syms)
    pn = {
        "open": C.shift(1).fillna(C.iloc[0]),
        "high": C * 1.01,
        "low": C * 0.99,
        "close": C,
        "volume": pd.DataFrame(rng.uniform(1e3, 1e5, size=(n_rows, n_syms)), index=idx, columns=syms),
        "quote_volume": pd.DataFrame(rng.uniform(1e6, 1e8, size=(n_rows, n_syms)), index=idx, columns=syms),
        "trades": pd.DataFrame(rng.uniform(10, 1000, size=(n_rows, n_syms)), index=idx, columns=syms),
        "taker_buy_volume": pd.DataFrame(rng.uniform(1e2, 1e4, size=(n_rows, n_syms)), index=idx, columns=syms),
        "taker_buy_quote_volume": pd.DataFrame(rng.uniform(1e5, 1e7, size=(n_rows, n_syms)), index=idx, columns=syms),
    }
    elig = pd.DataFrame(True, index=idx, columns=syms)
    aux = {"eligibility": elig, "seed": 0}
    return pn, aux


def _weights(pn, aux):
    return strategy.build_raw_weights(pn, aux)


# --------------------------------------------------------------------------- determinism -------
def test_determinism_bit_identical():
    pn, aux = _panels()
    w1 = _weights(pn, aux)
    w2 = _weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


# ---------------------------------------------------------------------- future-corruption ------
def test_future_corruption_klines_and_eligibility():
    """Mangle close AND eligibility STRICTLY AFTER a cut; weights at/before the cut unchanged."""
    pn, aux = _panels()
    w_full = _weights(pn, aux)

    cut_pos = 300
    idx = pn["close"].index
    cut = idx[cut_pos]
    after = idx > cut

    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[after] = pn_c["close"].loc[after] * 7.0 + 5.0
    aux_c = {"eligibility": aux["eligibility"].copy(), "seed": aux["seed"]}
    aux_c["eligibility"].loc[after] = ~aux_c["eligibility"].loc[after]

    w_c = _weights(pn_c, aux_c)
    pd.testing.assert_frame_equal(
        w_full[w_full.index <= cut], w_c[w_c.index <= cut], check_exact=True
    )


def test_future_corruption_multiple_cuts():
    pn, aux = _panels()
    w_full = _weights(pn, aux)
    idx = pn["close"].index
    for cut_pos in (120, 200, 350):
        cut = idx[cut_pos]
        after = idx > cut
        pn_c = {k: v.copy() for k, v in pn.items()}
        pn_c["close"].loc[after] = pn_c["close"].loc[after] * 3.0 + 2.0
        aux_c = {"eligibility": aux["eligibility"].copy(), "seed": aux["seed"]}
        aux_c["eligibility"].loc[after] = ~aux_c["eligibility"].loc[after]
        w_c = _weights(pn_c, aux_c)
        pd.testing.assert_frame_equal(
            w_full[w_full.index <= cut], w_c[w_c.index <= cut], check_exact=True
        )


# ---------------------------------------------------------------------------- same-bar ---------
def test_samebar_before_tstar_unchanged():
    """Perturb close at candle t* only; weights STRICTLY BEFORE t* must be unchanged."""
    pn, aux = _panels()
    w_full = _weights(pn, aux)
    idx = pn["close"].index
    t_star = idx[280]

    pn_p = {k: v.copy() for k, v in pn.items()}
    pn_p["close"].loc[t_star] = pn_p["close"].loc[t_star] * 1.001

    w_p = _weights(pn_p, aux)
    pd.testing.assert_frame_equal(
        w_full[w_full.index < t_star], w_p[w_p.index < t_star], check_exact=True
    )


# ---------------------------------------------------------------------------- widening ---------
def test_widening_extra_column_flat_no_crash():
    """Extra never-eligible synthetic column must not crash and must stay flat (all zero)."""
    pn, aux = _panels()
    idx = pn["close"].index
    n = len(idx)
    rng = np.random.default_rng(99)
    extra_px = 10.0 * np.exp(np.cumsum(rng.normal(0, 0.01, size=n)))
    pn_w = {k: v.copy() for k, v in pn.items()}
    for k in pn_w:
        pn_w[k] = pn_w[k].copy()
        pn_w[k]["ZZWIDE00"] = extra_px if k in ("open", "high", "low", "close") else rng.uniform(
            1e3, 1e5, size=n
        )
    # eligibility NOT widened -> the synthetic column is never eligible.
    w = _weights(pn_w, aux)
    assert isinstance(w, pd.DataFrame)
    assert "ZZWIDE00" in w.columns
    assert (w["ZZWIDE00"] == 0.0).all()


# ------------------------------------------------------------------------- NaN-tolerance -------
def test_nan_column_flat():
    """An all-NaN young/dead column must never take weight, even when marked eligible."""
    pn, aux = _panels()
    pn_n = {k: v.copy() for k, v in pn.items()}
    dead = pn_n["close"].columns[0]
    for k in pn_n:
        pn_n[k] = pn_n[k].copy()
        pn_n[k][dead] = np.nan
    w = _weights(pn_n, aux)
    assert (w[dead] == 0.0).all()
    # the rest of the book is unaffected structurally: still finite everywhere.
    assert np.isfinite(w.to_numpy()).all()


# ---------------------------------------------------------- structural invariants (spec) -------
def test_row_demean_and_sign():
    """Row net ~ 0 (cross-sectional) and the sign is long high-expansion / short low."""
    pn, aux = _panels()
    w = _weights(pn, aux)
    active = w.abs().sum(axis=1) > 0
    row_net = w[active].sum(axis=1)
    assert row_net.abs().max() < 1e-9  # demeaned -> row net exactly zero (float noise)

    # sign check on a warmed row: highest smoothed expansion ratio must carry the max weight.
    C = pn["close"]
    r = np.log(C).diff()
    vt = (r.rolling(12, min_periods=9).std() / r.rolling(84, min_periods=63).std()).replace(
        [np.inf, -np.inf], np.nan
    )
    sm = vt.ewm(halflife=72, min_periods=1, adjust=True, ignore_na=False).mean()
    row = w.index[-1]
    top_sym = sm.loc[row].idxmax()
    bot_sym = sm.loc[row].idxmin()
    assert w.loc[row, top_sym] == w.loc[row].max()
    assert w.loc[row, bot_sym] == w.loc[row].min()
    assert w.loc[row, top_sym] > 0 > w.loc[row, bot_sym]


def test_warmup_rows_flat():
    """Before the long-vol min_periods warms up, the book is entirely flat."""
    pn, aux = _panels()
    w = _weights(pn, aux)
    # vol_l needs min_periods=63 on diff'd returns -> earliest non-flat row index >= 63.
    early = w.iloc[:63]
    assert (early.to_numpy() == 0.0).all()
