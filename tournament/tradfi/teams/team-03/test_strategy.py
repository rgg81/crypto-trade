"""team-03 strategy tests — leak-proofing self-checks on synthetic panels.

Covers (all mandatory for freeze, mirroring the mechanical harness on team-owned inputs):
  * determinism            — two fresh calls on identical inputs are bit-identical
  * future corruption      — mangle every bar STRICTLY AFTER a cut; weights <= cut unchanged
  * truncated replay       — truncate the panel at a cut; weights <= cut unchanged
  * same-bar               — perturb close[t*]; weights STRICTLY BEFORE t* unchanged
  * no hard-coded tickers  — columns are taken from the panel at runtime
  * ragged starts          — a late-starting name is flat (NaN) through its warmup; no infs

These use synthetic data so the tests are fast and self-contained; the tournament's own
`cli.py audit` re-runs the same five checks against the frozen IS snapshot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# pytest's default "prepend" import mode puts this team dir on sys.path, so the sibling
# strategy module resolves directly — no stdlib path/import machinery (which the static
# scan bans) is needed.
from strategy import build_raw_weights


# ------------------------------------------------------------------ fixtures -------------------
def _make_panels(
    seed: int = 0,
    n_days: int = 400,
    tickers: list[str] | None = None,
    ragged: dict[str, int] | None = None,
) -> tuple[dict[str, pd.DataFrame], dict]:
    """Synthetic OHLCV panels + VIX/sector aux. Only close/vix/sector_map are consumed by the
    strategy; the rest are present to prove they are ignored and never crash the pipeline."""
    if tickers is None:
        tickers = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"]
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n_days)
    rets = rng.normal(0.0, 0.02, size=(n_days, len(tickers)))
    close = pd.DataFrame(100.0 * np.exp(np.cumsum(rets, axis=0)), index=idx, columns=tickers)
    if ragged:
        for tk, k in ragged.items():
            close.iloc[:k, close.columns.get_loc(tk)] = np.nan
    high = close * (1.0 + np.abs(rng.normal(0.0, 0.005, size=close.shape)))
    low = close * (1.0 - np.abs(rng.normal(0.0, 0.005, size=close.shape)))
    open_ = close.shift(1).where(close.shift(1).notna(), close)
    volume = pd.DataFrame(rng.uniform(1e6, 5e6, size=close.shape), index=idx, columns=tickers)
    pn = {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    # VIX with genuine dispersion so the rolling-252d percentile gate (> 0.85) fires on ~15% of
    # days once past the 126-day warmup — the book must actually trade before any test cut.
    vix = pd.Series(10.0 + 15.0 * np.abs(rng.normal(0.0, 1.0, size=n_days)), index=idx)
    sector_map = {tk: ("SEC_A" if i % 2 == 0 else "SEC_B") for i, tk in enumerate(tickers)}
    aux = {"vix": vix, "sector_map": sector_map, "seed": 20260717}
    return pn, aux


def _corrupt_after(pn, aux, cut):
    """Mangle every bar STRICTLY AFTER the cut (prices x7+5, volume x3+1, VIX x2+3)."""
    out_pn = {}
    for k, df in pn.items():
        d = df.copy()
        mask = d.index > cut
        d.loc[mask, :] = d.loc[mask, :] * (3.0 if k == "volume" else 7.0) + (1.0 if k == "volume" else 5.0)
        out_pn[k] = d
    v = aux["vix"].copy()
    v.loc[v.index > cut] = v.loc[v.index > cut] * 2.0 + 3.0
    return out_pn, {**aux, "vix": v}


def _truncate(pn, aux, cut):
    out_pn = {k: df[df.index <= cut].copy() for k, df in pn.items()}
    v = aux["vix"]
    return out_pn, {**aux, "vix": v[v.index <= cut].copy()}


def _perturb_close(pn, aux, t):
    d = pn["close"].copy()
    d.loc[t, :] = d.loc[t, :] * 1.001
    return {**pn, "close": d}, aux


# ------------------------------------------------------------------ tests ----------------------
def test_determinism():
    pn, aux = _make_panels(seed=1)
    w1 = build_raw_weights(pn, aux)
    w2 = build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_future_corruption_before_cut_unchanged():
    pn, aux = _make_panels(seed=2)
    idx = pn["close"].index
    cut = idx[int(len(idx) * 0.7)]
    w_full = build_raw_weights(pn, aux)
    pn_c, aux_c = _corrupt_after(pn, aux, cut)
    w_c = build_raw_weights(pn_c, aux_c)
    a = w_full[w_full.index <= cut]
    b = w_c[w_c.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    # guard against a vacuous pass: the book must actually trade before the cut
    assert (a.fillna(0.0).abs().to_numpy() > 0).any()


def test_truncated_replay_before_cut_unchanged():
    pn, aux = _make_panels(seed=3)
    idx = pn["close"].index
    cut = idx[int(len(idx) * 0.6)]
    w_full = build_raw_weights(pn, aux)
    pn_t, aux_t = _truncate(pn, aux, cut)
    w_t = build_raw_weights(pn_t, aux_t)
    a = w_full[w_full.index <= cut]
    b = w_t[w_t.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    assert (a.fillna(0.0).abs().to_numpy() > 0).any()


def test_same_bar_before_tstar_unchanged():
    pn, aux = _make_panels(seed=4)
    idx = pn["close"].index
    t_star = idx[int(len(idx) * 0.7)]
    w_full = build_raw_weights(pn, aux)
    pn_p, aux_p = _perturb_close(pn, aux, t_star)
    w_p = build_raw_weights(pn_p, aux_p)
    a = w_full[w_full.index < t_star]
    b = w_p[w_p.index < t_star]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_no_hardcoded_tickers():
    tickers = ["ZZZ1", "QQQ2", "WWW3", "RRR4", "TTT5", "YYY6"]
    pn, aux = _make_panels(seed=5, tickers=tickers)
    w = build_raw_weights(pn, aux)
    assert list(w.columns) == tickers
    assert w.index.equals(pn["close"].index)


def test_ragged_starts_flat_and_finite():
    tickers = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
    pn, aux = _make_panels(seed=6, tickers=tickers, ragged={"CCC": 150})
    w = build_raw_weights(pn, aux)
    # late-starting name is flat (NaN = flat) through its missing-price prefix
    assert w["CCC"].iloc[:150].isna().all()
    # no infinities emitted anywhere (NaN is the only allowed "no value")
    vals = w.to_numpy()
    assert not np.isinf(vals[~np.isnan(vals)]).any()


def test_output_conforms_to_panel_grid():
    pn, aux = _make_panels(seed=7)
    w = build_raw_weights(pn, aux)
    assert isinstance(w, pd.DataFrame)
    assert w.index.equals(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)
