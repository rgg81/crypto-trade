"""team-01 strategy tests — t01-funding-carry-xs-v1.

Self-contained: builds synthetic candle x symbol panels (never reads any data file) and
exercises the frozen strategy directly. Every import stays inside the harness whitelist
(numpy / pandas / stdlib-math + the local ``strategy`` module) and every test is a plain
``assert`` function so no ``pytest`` import is needed (the static scan reads this file too).

Covers the QE-SPEC-mandated checks:
  (a) future corruption   — mangle klines AND aux (funding + eligibility) STRICTLY after a
                            cut; weights at/before the cut are bit-unchanged.
  (b) determinism         — two calls on deep copies are ``.equals()``-identical.
  (c) widening            — an extra synthetic column in pn (and separately in aux) neither
                            crashes nor changes the real columns' weights.
  (d) NaN tolerance       — an all-NaN column stays all-zero in the output.
  (e) shape/index/columns — output aligns to pn["close"] with no residual NaNs.
Plus truncated-replay (past-only) and mechanism-sign sanity checks.
"""

import numpy as np
import pandas as pd

import strategy

STEP = "8h"


def _make_panels(seed=7, n=240, symbols=None, dead_col=True, late_listers=True):
    """Deterministic synthetic (pn, aux). Positive random-walk prices, small funding,
    eligibility = alive within the top-40 (here: all alive names). One optional all-NaN
    'dead' column and a couple of late-listing columns to exercise the masks."""
    if symbols is None:
        symbols = [f"C{i:02d}USDT" for i in range(8)]
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-01-01", periods=n, freq=STEP)

    close = pd.DataFrame(index=idx, columns=symbols, dtype=float)
    for j, s in enumerate(symbols):
        steps = rng.normal(0.0, 0.01, size=n)
        px = 10.0 * (1.0 + j) * np.exp(np.cumsum(steps))
        close[s] = px

    if late_listers and len(symbols) >= 3:
        # two names list mid-panel: close is NaN before they exist
        close.iloc[:30, 1] = np.nan
        close.iloc[:55, 2] = np.nan
    if dead_col:
        close[symbols[-1]] = np.nan  # a never-traded name

    alive = close.notna()

    # funding: small autocorrelated series, 0.0 where the name never traded (engine convention)
    fund = pd.DataFrame(index=idx, columns=symbols, dtype=float)
    for j, s in enumerate(symbols):
        base = rng.normal(0.0, 1e-4, size=n).cumsum() * 0.02 + (j - 3.5) * 5e-5
        fund[s] = base
    fund = fund.where(alive, 0.0)

    elig = alive.copy()  # in-force top-40 == alive here

    pn = {
        "open": close.shift(1).fillna(close),
        "high": close * 1.005,
        "low": close * 0.995,
        "close": close,
        "volume": pd.DataFrame(rng.uniform(1e3, 1e5, size=(n, len(symbols))), index=idx,
                               columns=symbols).where(alive, np.nan),
        "quote_volume": pd.DataFrame(rng.uniform(1e6, 1e8, size=(n, len(symbols))), index=idx,
                                     columns=symbols).where(alive, np.nan),
        "trades": pd.DataFrame(rng.uniform(10, 1e4, size=(n, len(symbols))), index=idx,
                               columns=symbols).where(alive, np.nan),
        "taker_buy_volume": pd.DataFrame(rng.uniform(1e2, 1e4, size=(n, len(symbols))), index=idx,
                                         columns=symbols).where(alive, np.nan),
        "taker_buy_quote_volume": pd.DataFrame(rng.uniform(1e5, 1e7, size=(n, len(symbols))),
                                               index=idx, columns=symbols).where(alive, np.nan),
    }
    aux = {"funding": fund, "eligibility": elig, "seed": 12345}
    return pn, aux


def _copy_pn(pn):
    return {k: v.copy() for k, v in pn.items()}


def _copy_aux(aux):
    return {k: (v.copy() if isinstance(v, (pd.DataFrame, pd.Series)) else v) for k, v in aux.items()}


# ---------------------------------------------------------------- (e) shape ---------------------
def test_output_shape_index_columns():
    pn, aux = _make_panels()
    w = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))
    close = pn["close"]
    assert isinstance(w, pd.DataFrame)
    assert w.index.equals(close.index)
    assert list(w.columns) == list(close.columns)
    # spec binding note 1: the final re-mask leaves NO NaNs
    assert bool(w.notna().to_numpy().all())


# ---------------------------------------------------------------- (b) determinism ---------------
def test_determinism():
    pn, aux = _make_panels(seed=3)
    w1 = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))
    w2 = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))
    assert w1.equals(w2)


# ---------------------------------------------------------------- (a) future corruption ---------
def test_future_corruption_klines_and_aux():
    pn, aux = _make_panels(seed=11)
    w_full = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))

    cut_pos = 150
    idx = pn["close"].index
    cut = idx[cut_pos]

    pn_c = _copy_pn(pn)
    aux_c = _copy_aux(aux)
    after = slice(cut_pos + 1, None)
    # klines: mangle EVERY panel row strictly after the cut (prices x7+5, else x3+1)
    for k, df in pn_c.items():
        mult, add = (7.0, 5.0) if k in ("open", "high", "low", "close") else (3.0, 1.0)
        df.iloc[after] = df.iloc[after] * mult + add
    # aux: funding x3+1e-4, eligibility inverted — all STRICTLY after the cut
    aux_c["funding"].iloc[after] = aux_c["funding"].iloc[after] * 3.0 + 1e-4
    aux_c["eligibility"].iloc[after] = ~aux_c["eligibility"].iloc[after]

    w_corr = strategy.build_raw_weights(pn_c, aux_c)

    a = w_full[w_full.index <= cut]
    b = w_corr[w_corr.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    # belt-and-suspenders numeric check
    assert np.allclose(a.to_numpy(), b.to_numpy(), rtol=0.0, atol=0.0)


# ---------------------------------------------------------------- truncated replay (past-only) --
def test_truncated_replay():
    pn, aux = _make_panels(seed=5)
    w_full = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))

    cut_pos = 170
    idx = pn["close"].index
    cut = idx[cut_pos]

    pn_t = {k: v[v.index <= cut].copy() for k, v in pn.items()}
    aux_t = {
        "funding": aux["funding"][aux["funding"].index <= cut].copy(),
        "eligibility": aux["eligibility"][aux["eligibility"].index <= cut].copy(),
        "seed": aux["seed"],
    }
    w_trunc = strategy.build_raw_weights(pn_t, aux_t)

    a = w_full[w_full.index <= cut]
    pd.testing.assert_frame_equal(a, w_trunc, check_exact=True)


# ---------------------------------------------------------------- (c) widening: extra pn col ----
def test_widening_extra_pn_column():
    pn, aux = _make_panels(seed=9)
    w_ref = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))

    pn_w = _copy_pn(pn)
    idx = pn_w["close"].index
    rng = np.random.default_rng(99)
    newcol = "ZZWIDE00USDT"
    for k, df in pn_w.items():
        vals = rng.uniform(1.0, 100.0, size=len(idx))
        df[newcol] = vals  # extra symbol present ONLY in pn, never eligible in aux
    aux_w = _copy_aux(aux)  # aux has NO column for the new symbol -> reindex fills it, elig False

    w_new = strategy.build_raw_weights(pn_w, aux_w)
    assert newcol in w_new.columns
    # never-eligible synthetic name must be flat
    assert bool((w_new[newcol] == 0.0).to_numpy().all())
    # real columns unchanged
    pd.testing.assert_frame_equal(w_new[w_ref.columns], w_ref, check_exact=True)


# ---------------------------------------------------------------- (c) widening: extra aux col ---
def test_widening_extra_aux_column():
    pn, aux = _make_panels(seed=13)
    w_ref = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))

    aux_w = _copy_aux(aux)
    idx = aux_w["funding"].index
    extra = "QQEXTRAUSDT"  # symbol present ONLY in aux, absent from pn -> must be ignored
    aux_w["funding"][extra] = 1.0
    aux_w["eligibility"][extra] = True

    w_new = strategy.build_raw_weights(_copy_pn(pn), aux_w)
    assert extra not in w_new.columns
    pd.testing.assert_frame_equal(w_new, w_ref, check_exact=True)


# ---------------------------------------------------------------- (d) NaN tolerance -------------
def test_nan_column_stays_zero():
    pn, aux = _make_panels(seed=21)
    w = strategy.build_raw_weights(_copy_pn(pn), _copy_aux(aux))
    dead = pn["close"].columns[-1]  # the all-NaN 'dead' name
    assert bool(pn["close"][dead].isna().all())
    assert bool((w[dead] == 0.0).to_numpy().all())
    # an entirely NaN aux funding panel must not crash and yields an all-zero book
    pn2, aux2 = _make_panels(seed=22)
    aux2["funding"] = aux2["funding"] * np.nan
    w2 = strategy.build_raw_weights(pn2, aux2)
    assert w2.shape == pn2["close"].shape
    assert bool((w2.to_numpy() == 0.0).all())


# ---------------------------------------------------------------- mechanism sign ----------------
def test_signal_sign_shorts_high_funding():
    # constant funding ordering over time -> stable rank -> sign is unambiguous at the last row
    symbols = [f"S{i:02d}USDT" for i in range(8)]
    n = 120
    idx = pd.date_range("2022-01-01", periods=n, freq=STEP)
    rng = np.random.default_rng(4)
    close = pd.DataFrame(index=idx, columns=symbols, dtype=float)
    fund = pd.DataFrame(index=idx, columns=symbols, dtype=float)
    for j, s in enumerate(symbols):
        close[s] = 10.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, size=n)))
        fund[s] = (j - 3.5) * 1e-4  # S00 most negative funding ... S07 most positive
    elig = pd.DataFrame(True, index=idx, columns=symbols)
    pn = {"close": close}
    for k in ("open", "high", "low"):
        pn[k] = close.copy()
    for k in ("volume", "quote_volume", "trades", "taker_buy_volume", "taker_buy_quote_volume"):
        pn[k] = pd.DataFrame(1.0, index=idx, columns=symbols)
    aux = {"funding": fund, "eligibility": elig, "seed": 0}

    w = strategy.build_raw_weights(pn, aux)
    last = w.iloc[-1]
    assert last["S07USDT"] < 0.0  # highest funding -> short
    assert last["S00USDT"] > 0.0  # lowest funding  -> long
    assert abs(last.sum()) < abs(last.abs().sum())  # a genuine long/short book, not one-sided
