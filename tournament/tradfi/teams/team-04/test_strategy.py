"""team-04 strategy self-checks — t04-xs-momentum-12-1-v1.

Imports restricted to the audit scan whitelist: numpy, pandas, and the local ``strategy``
module. No ``import pytest`` (pytest discovers plain ``test_*`` functions without it), no file
I/O, no network. These are the brief §5 mandatory self-checks (future-corruption + determinism)
plus truncated-replay and same-bar causality checks that mirror the mechanical harness, run on a
self-contained synthetic panel so the tests never touch the frozen snapshot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategy import MIN_SIDE, build_raw_weights


# ------------------------------------------------------------------ synthetic panel ------------
def _make_panel(n_rows: int = 420, n_cols: int = 30, seed: int = 7) -> dict:
    """Geometric-random-walk close panel (DatetimeIndex x tickers), plus a few ragged starts so
    eligibility, the 252-row warmup, and the min-5-per-side floor all exercise real branches."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n_rows)
    cols = [f"SYM{i:02d}" for i in range(n_cols)]
    steps = rng.normal(0.0005, 0.02, size=(n_rows, n_cols))
    close = pd.DataFrame(100.0 * np.exp(np.cumsum(steps, axis=0)), index=idx, columns=cols)
    # Ragged starts: a couple of names appear late (NaN before their first bar).
    close.iloc[:40, 0] = np.nan
    close.iloc[:120, 1] = np.nan
    return {"close": close}


def _aux(seed: int = 20260717) -> dict:
    return {"vix": None, "sector_map": {}, "seed": seed}


def _active_rows(w: pd.DataFrame) -> pd.DataFrame:
    return w[w.abs().sum(axis=1) > 0]


# ------------------------------------------------------------------ determinism ----------------
def test_determinism_two_calls_identical():
    pn = _make_panel()
    a = build_raw_weights(pn, _aux())
    b = build_raw_weights(pn, _aux())
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_aux_is_unused():
    """Output must not depend on aux contents (seed / vix / sector_map) — the strategy is a pure
    function of the price panel only."""
    pn = _make_panel()
    a = build_raw_weights(pn, {"vix": None, "sector_map": {}, "seed": 1})
    b = build_raw_weights(pn, {"vix": None, "sector_map": {}, "seed": 999999})
    pd.testing.assert_frame_equal(a, b, check_exact=True)


# ------------------------------------------------------------------ future corruption ----------
def test_future_corruption_leaves_past_unchanged():
    """Mangle every bar STRICTLY AFTER a cut (prices x7+5, the harness rule); weights at/before
    the cut must be bit-identical."""
    pn = _make_panel()
    w_full = build_raw_weights(pn, _aux())

    cut_pos = 320
    cut = pn["close"].index[cut_pos]
    close2 = pn["close"].copy()
    future = close2.index > cut
    close2.loc[future, :] = close2.loc[future, :] * 7.0 + 5.0
    w_corr = build_raw_weights({"close": close2}, _aux())

    a = w_full[w_full.index <= cut]
    b = w_corr[w_corr.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_future_corruption_at_multiple_cuts():
    pn = _make_panel()
    w_full = build_raw_weights(pn, _aux())
    for cut_pos in (260, 300, 380, len(pn["close"]) - 2):
        cut = pn["close"].index[cut_pos]
        close2 = pn["close"].copy()
        future = close2.index > cut
        close2.loc[future, :] = close2.loc[future, :] * 7.0 + 5.0
        w_corr = build_raw_weights({"close": close2}, _aux())
        pd.testing.assert_frame_equal(
            w_full[w_full.index <= cut], w_corr[w_corr.index <= cut], check_exact=True
        )


# ------------------------------------------------------------------ truncated replay -----------
def test_truncated_replay_equivalence():
    """Re-running on a panel truncated at the cut must reproduce weights <= cut bit-for-bit — the
    membership state must rebuild identically from history alone (no panel-length dependence)."""
    pn = _make_panel()
    w_full = build_raw_weights(pn, _aux())
    for cut_pos in (270, 350, len(pn["close"]) - 2):
        cut = pn["close"].index[cut_pos]
        trunc = {"close": pn["close"][pn["close"].index <= cut]}
        w_t = build_raw_weights(trunc, _aux())
        pd.testing.assert_frame_equal(
            w_full[w_full.index <= cut], w_t[w_t.index <= cut], check_exact=True
        )


# ------------------------------------------------------------------ same-bar causality ---------
def test_same_bar_perturbation_leaves_strict_past_unchanged():
    """Perturbing close[t*] may change the weight AT t* (legitimately available) but never any
    weight STRICTLY BEFORE t*."""
    pn = _make_panel()
    w_full = build_raw_weights(pn, _aux())
    t_pos = int(len(pn["close"]) * 0.7)
    t_star = pn["close"].index[t_pos]
    close2 = pn["close"].copy()
    close2.loc[t_star, :] = close2.loc[t_star, :] * 1.001
    w_p = build_raw_weights({"close": close2}, _aux())
    pd.testing.assert_frame_equal(
        w_full[w_full.index < t_star], w_p[w_p.index < t_star], check_exact=True
    )


# ------------------------------------------------------------------ output invariants ----------
def test_output_grid_and_dtype():
    pn = _make_panel()
    w = build_raw_weights(pn, _aux())
    assert list(w.index) == list(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)
    assert w.dtypes.map(lambda d: d.kind == "f").all()
    assert np.isfinite(w.to_numpy()).all()  # zeros where flat, never NaN


def test_warmup_rows_are_flat():
    """No name can be eligible before it has FORMATION prior rows; the first 252 rows are flat."""
    pn = _make_panel()
    w = build_raw_weights(pn, _aux())
    assert (w.iloc[:252].abs().sum(axis=1) == 0).all()


def test_equal_weight_dollar_balance_on_active_rows():
    """On every active row: long side sums to +1, short side to -1 (equal-weight tails), and each
    side holds >= MIN_SIDE names."""
    pn = _make_panel()
    w = build_raw_weights(pn, _aux())
    act = _active_rows(w)
    assert len(act) > 0
    pos = act.clip(lower=0.0).sum(axis=1)
    neg = act.clip(upper=0.0).sum(axis=1)
    assert np.allclose(pos.to_numpy(), 1.0)
    assert np.allclose(neg.to_numpy(), -1.0)
    n_long = (act > 0).sum(axis=1)
    n_short = (act < 0).sum(axis=1)
    assert (n_long >= MIN_SIDE).all()
    assert (n_short >= MIN_SIDE).all()


def test_no_name_both_long_and_short():
    pn = _make_panel()
    w = build_raw_weights(pn, _aux())
    # A name is never simultaneously long and short (impossible for a single scalar weight, but
    # guards against any future refactor emitting conflicting signs within a row).
    assert ((w > 0) & (w < 0)).to_numpy().sum() == 0
