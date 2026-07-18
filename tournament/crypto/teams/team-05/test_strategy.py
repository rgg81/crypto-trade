"""team-05 tests — QE SPEC section 9 mandated assertions.

Self-contained: only numpy/pandas/stdlib + a plain ``import strategy`` (the static scan
whitelists nothing else, and the evaluator package is off-limits to team code). Synthetic
8h panels are built here; the checks are strategy-specific, not generic harness stand-ins.

Run: uv run pytest tournament/crypto/teams/team-05/test_strategy.py -q
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

_PANELS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades",
    "taker_buy_volume",
    "taker_buy_quote_volume",
)


def _make_panels(n_rows: int = 220, n_syms: int = 8, seed: int = 7):
    """Deterministic synthetic panels + aux on the 8h grid (share varies so ranks are real)."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n_rows, freq="8h")
    syms = [f"{chr(65 + i)}{chr(65 + i)}{chr(65 + i)}USDT" for i in range(n_syms)]

    px = 10.0 * np.exp(np.cumsum(rng.normal(0, 0.01, size=(n_rows, n_syms)), axis=0))
    qv = rng.uniform(1e5, 1e7, size=(n_rows, n_syms))
    share = rng.uniform(0.2, 0.8, size=(n_rows, n_syms))  # aggressive-buy share per cell
    tbq = qv * share

    def _df(a):
        return pd.DataFrame(a, index=idx, columns=syms)

    pn = {
        "open": _df(px),
        "high": _df(px * 1.01),
        "low": _df(px * 0.99),
        "close": _df(px * (1 + rng.normal(0, 0.001, size=(n_rows, n_syms)))),
        "volume": _df(qv / px),
        "quote_volume": _df(qv),
        "trades": _df(rng.uniform(50, 5000, size=(n_rows, n_syms))),
        "taker_buy_volume": _df(tbq / px),
        "taker_buy_quote_volume": _df(tbq),
    }

    elig = pd.DataFrame(True, index=idx, columns=syms)
    elig.iloc[100] = False  # a fully-ineligible row (expect a flat weights row)
    elig.iloc[120] = False
    elig.iloc[120, 3] = True  # a single-eligible-name row (expect flat: demeaned singleton = 0)

    funding = pd.DataFrame(
        rng.normal(0, 1e-4, size=(n_rows, n_syms)), index=idx, columns=syms
    )
    aux = {"eligibility": elig, "funding": funding, "seed": 12345}
    return pn, aux, idx


def _copy_pn(pn):
    return {k: v.copy() for k, v in pn.items()}


# --------------------------------------------------------------------- determinism -------------
def test_determinism_bit_identical():
    pn, aux, _ = _make_panels()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


# --------------------------------------------------------------- index/column contract ---------
def test_output_index_columns_match_open():
    pn, aux, _ = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_index_equal(w.index, pn["open"].index)
    pd.testing.assert_index_equal(w.columns, pn["open"].columns)


# --------------------------------------------------------------- past-only / corruption --------
def test_future_corruption_klines_and_aux():
    """Mangle klines AND aux STRICTLY after a cut; every row <= cut must be bit-identical."""
    pn, aux, idx = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)

    cut_pos = 150
    cut_ts = idx[cut_pos]
    fut = idx > cut_ts

    pn_c = _copy_pn(pn)
    for k in ("open", "high", "low", "close"):
        pn_c[k].loc[fut] = pn_c[k].loc[fut] * 7.0 + 5.0
    for k in ("volume", "quote_volume", "trades", "taker_buy_volume"):
        pn_c[k].loc[fut] = pn_c[k].loc[fut] * 3.0 + 1.0
    # a DIFFERENT factor on the numerator flips the aggressive-buy ratio after the cut too
    pn_c["taker_buy_quote_volume"].loc[fut] = pn_c["taker_buy_quote_volume"].loc[fut] * 5.0 + 7.0

    aux_c = dict(aux)
    elig_c = aux["eligibility"].copy()
    elig_c.loc[fut] = ~elig_c.loc[fut].astype(bool)  # invert future eligibility
    aux_c["eligibility"] = elig_c
    fund_c = aux["funding"].copy()
    fund_c.loc[fut] = fund_c.loc[fut] * 3.0 + 1e-4
    aux_c["funding"] = fund_c

    w_corr = strategy.build_raw_weights(pn_c, aux_c)
    pd.testing.assert_frame_equal(
        w_full.loc[:cut_ts], w_corr.loc[:cut_ts], check_exact=True
    )


# ------------------------------------------------------------------------- widening ------------
def test_widening_extra_columns_inert():
    """Extra never-eligible synthetic columns must not crash nor change existing columns."""
    pn, aux, idx = _make_panels()
    w_base = strategy.build_raw_weights(pn, aux)
    orig_cols = list(pn["open"].columns)

    rng = np.random.default_rng(99)
    n = len(idx)
    pn_w = _copy_pn(pn)
    wide = [f"ZZWIDE{i:02d}USDT" for i in range(4)]
    for name in wide:
        px = 10.0 * np.exp(np.cumsum(rng.normal(0, 0.01, size=n)))
        vol = rng.uniform(1e3, 1e5, size=n)
        pn_w["open"][name] = px
        pn_w["high"][name] = px * 1.01
        pn_w["low"][name] = px * 0.99
        pn_w["close"][name] = px
        pn_w["volume"][name] = vol
        pn_w["quote_volume"][name] = vol * px
        pn_w["trades"][name] = 100.0
        pn_w["taker_buy_volume"][name] = vol * 0.5
        pn_w["taker_buy_quote_volume"][name] = vol * px * 0.5

    aux_w = dict(aux)
    elig_w = aux["eligibility"].copy()
    for name in wide:
        elig_w[name] = False  # never eligible, like a holdout coin absent from the mask
    aux_w["eligibility"] = elig_w

    w_wide = strategy.build_raw_weights(pn_w, aux_w)
    assert isinstance(w_wide, pd.DataFrame)
    assert list(w_wide.columns) == orig_cols + wide
    # the synthetic never-eligible names carry no weight
    assert (w_wide[wide].abs().to_numpy() == 0.0).all()
    # existing columns' weights are bit-identical (NaN columns are excluded from the rank)
    pd.testing.assert_frame_equal(w_wide[orig_cols], w_base, check_exact=True)


# --------------------------------------------------------------- degenerate flat rows ----------
def test_empty_eligibility_and_singleton_rows_flat():
    pn, aux, idx = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    # fully-ineligible row -> flat
    assert (w.iloc[100].to_numpy() == 0.0).all()
    # single-eligible-name row -> flat (a demeaned singleton is exactly 0)
    assert (w.iloc[120].to_numpy() == 0.0).all()


def test_warmup_rows_flat():
    """Rows before MIN_PERIODS of history have all-NaN signal -> flat weights."""
    pn, aux, _ = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    assert (w.iloc[: strategy.MIN_PERIODS - 1].to_numpy() == 0.0).all()


def test_rows_sum_to_zero_when_active():
    """Any active (non-flat) row is a demeaned book -> sums to ~0 (sum-zero long/short)."""
    pn, aux, _ = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    row_sums = w.sum(axis=1).to_numpy()
    active = w.abs().sum(axis=1).to_numpy() > 0
    assert np.allclose(row_sums[active], 0.0, atol=1e-12)
    assert active.any()  # the strategy actually trades on this synthetic panel
