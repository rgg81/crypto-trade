"""team-09 strategy tests (research_brief.md Section 9 mandated checks).

Self-contained: builds deterministic synthetic panels with numpy/pandas only and drives
`build_raw_weights` directly. No evaluator import, no file reads, no pytest import (pytest
discovers plain ``test_*`` functions) — so this file also passes the harness static scan.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

PANEL_KEYS = (
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


def _make_panels(n_rows: int = 320, n_syms: int = 16, seed: int = 7):
    """Deterministic 8h panels: positive quote_volume + trades, all-eligible names."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n_rows, freq="8h")
    syms = [f"SYM{i:02d}" for i in range(n_syms)]

    px = pd.DataFrame(
        10.0 * np.exp(np.cumsum(rng.normal(0.0, 0.02, size=(n_rows, n_syms)), axis=0)),
        index=idx,
        columns=syms,
    )
    qv = pd.DataFrame(
        rng.lognormal(15.0, 1.0, size=(n_rows, n_syms)), index=idx, columns=syms
    )
    tr = pd.DataFrame(
        rng.integers(50, 5000, size=(n_rows, n_syms)).astype(float), index=idx, columns=syms
    )
    vol = qv / px
    pn = {
        "open": px,
        "high": px * 1.01,
        "low": px * 0.99,
        "close": px,
        "volume": vol,
        "quote_volume": qv,
        "trades": tr,
        "taker_buy_volume": vol * 0.5,
        "taker_buy_quote_volume": qv * 0.5,
    }
    elig = pd.DataFrame(True, index=idx, columns=syms)
    aux = {"eligibility": elig, "seed": 12345}
    return pn, aux, idx, syms


def test_output_contract():
    pn, aux, idx, syms = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    assert isinstance(w, pd.DataFrame)
    assert list(w.index) == list(idx)
    assert list(w.columns) == list(syms)
    # warmup rows (< W + B shift) are entirely flat; later rows carry signal.
    assert w.iloc[:110].isna().all().all()
    assert w.iloc[150:].notna().any().any()


def test_determinism():
    pn, aux, _, _ = _make_panels()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)
    # fresh inputs, same generator seed -> bit-identical output (no hidden state / clock / rng).
    pn2, aux2, _, _ = _make_panels()
    w3 = strategy.build_raw_weights(pn2, aux2)
    pd.testing.assert_frame_equal(w1, w3, check_exact=True)


def test_future_corruption_klines_and_aux():
    """Mangle klines AND aux strictly AFTER a cut; weights at/before the cut are unchanged."""
    pn, aux, idx, syms = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)

    cut = idx[200]
    after = idx > cut

    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["quote_volume"].loc[after] = pn_c["quote_volume"].loc[after] * 7.0 + 5.0
    pn_c["trades"].loc[after] = pn_c["trades"].loc[after] * 3.0 + 1.0
    for k in ("open", "high", "low", "close", "volume",
              "taker_buy_volume", "taker_buy_quote_volume"):
        pn_c[k].loc[after] = pn_c[k].loc[after] * 11.0 + 3.0
    aux_c = {"eligibility": aux["eligibility"].copy(), "seed": aux["seed"]}
    aux_c["eligibility"].loc[after] = ~aux_c["eligibility"].loc[after]

    w_corr = strategy.build_raw_weights(pn_c, aux_c)
    pd.testing.assert_frame_equal(
        w_full[w_full.index <= cut], w_corr[w_corr.index <= cut], check_exact=True
    )


def test_truncation_past_only():
    """Truncating every input after a cut leaves weights at/before the cut bit-identical."""
    pn, aux, idx, _ = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)

    cut = idx[230]
    keep = idx <= cut
    pn_t = {k: v[keep].copy() for k, v in pn.items()}
    aux_t = {"eligibility": aux["eligibility"][keep].copy(), "seed": aux["seed"]}
    w_trunc = strategy.build_raw_weights(pn_t, aux_t)
    pd.testing.assert_frame_equal(
        w_full[w_full.index <= cut], w_trunc[w_trunc.index <= cut], check_exact=True
    )


def test_min_names_guard():
    """A warmed row with fewer than MIN_NAMES eligible names is flat; a full row is active."""
    pn, aux, idx, syms = _make_panels(n_syms=16)
    elig = aux["eligibility"].copy()
    thin = idx[250]
    elig.loc[thin] = False
    elig.loc[thin, syms[:6]] = True  # only 6 eligible -> below MIN_NAMES=10
    aux2 = {"eligibility": elig, "seed": aux["seed"]}
    w = strategy.build_raw_weights(pn, aux2)
    assert w.loc[thin].isna().all()
    assert w.loc[idx[251]].notna().any()


def test_column_agnostic_widening():
    """An appended never-eligible column does not crash and does not perturb the others."""
    pn, aux, idx, syms = _make_panels()
    w_base = strategy.build_raw_weights(pn, aux)

    extra = "ZZWIDE00SYNTH"
    pn_w = {k: v.copy() for k, v in pn.items()}
    for k in PANEL_KEYS:
        pn_w[k][extra] = pn_w[k][syms[0]].to_numpy()
    elig = aux["eligibility"].copy()
    elig[extra] = False
    aux_w = {"eligibility": elig, "seed": aux["seed"]}

    w_wide = strategy.build_raw_weights(pn_w, aux_w)
    assert isinstance(w_wide, pd.DataFrame)
    assert extra in w_wide.columns
    assert w_wide[extra].isna().all()
    pd.testing.assert_frame_equal(w_wide[syms], w_base[syms], check_exact=True)


def test_row_centering_and_two_sided():
    """Active rows are cross-sectionally centered (sum ~ 0) and carry both long and short legs."""
    pn, aux, _, _ = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    active = w.dropna(how="all")
    assert len(active) > 0
    row_sums = active.sum(axis=1).to_numpy()
    assert np.allclose(row_sums, 0.0, atol=1e-9)
    assert (active > 0).sum(axis=1).min() >= 1
    assert (active < 0).sum(axis=1).min() >= 1
