"""team-10 strategy self-tests — determinism + strategy-specific future-corruption.

Constraints mirror the mechanical scan: this file may import only numpy / pandas / stdlib
and the team-local ``strategy`` module (no test framework import, no evaluator import). Tests
are plain ``assert``-based functions discoverable by the runner. Inputs are synthetic panels
built in-process; no file reads.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

STEP = "8h"
L, B, H = strategy.L, strategy.B, strategy.H


def _make_panels(n_rows: int = 260, n_syms: int = 10, seed: int = 0):
    """Synthetic close / quote_volume / eligibility on the 8h grid.

    Enough rows to clear the B + L participation warmup with room for post-warmup checks.
    One name is made permanently ineligible to exercise the mask.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n_rows, freq=STEP)
    syms = [f"SYM{i:02d}USDT" for i in range(n_syms)]

    rets = rng.normal(0.0, 0.02, size=(n_rows, n_syms))
    close = pd.DataFrame(100.0 * np.exp(np.cumsum(rets, axis=0)), index=idx, columns=syms)
    qv = pd.DataFrame(rng.uniform(1e5, 1e7, size=(n_rows, n_syms)), index=idx, columns=syms)

    elig = pd.DataFrame(True, index=idx, columns=syms)
    elig.iloc[:, -1] = False          # one permanently ineligible name
    elig.iloc[:3, :] = False          # thin early rows

    pn = {
        "open": close.copy(),
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": qv / 100.0,
        "quote_volume": qv,
    }
    aux = {"eligibility": elig, "seed": seed}
    return pn, aux


def test_determinism():
    """Two fresh calls on identical inputs must emit bit-identical weights."""
    pn, aux = _make_panels()
    a = strategy.build_raw_weights(pn, aux)
    b = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_output_shape_and_finite():
    """Output is a float DataFrame on the close grid, fully finite (no NaN residue)."""
    pn, aux = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    assert isinstance(w, pd.DataFrame)
    assert list(w.index) == list(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)
    assert np.isfinite(w.to_numpy()).all()


def test_permanently_ineligible_name_is_flat():
    """A name ineligible on every candle contributes exactly zero weight throughout."""
    pn, aux = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    dead = pn["close"].columns[-1]  # the permanently-ineligible name
    assert (w[dead] == 0.0).all()


def test_future_corruption_klines_and_aux():
    """Mangle klines AND aux strictly AFTER a cut; weights at/before the cut are unchanged.

    Prices x7+5, volumes x3+1, eligibility inverted on every row after the cut — exactly the
    adversarial mangling the mechanical harness applies. A past-only signal cannot see any of
    it, so every value dated at or before the cut must be bit-identical.
    """
    pn, aux = _make_panels()
    full = strategy.build_raw_weights(pn, aux)

    cut = pn["close"].index[170]

    pn2 = {k: v.copy() for k, v in pn.items()}
    mask = pn2["close"].index > cut
    for name in ("open", "high", "low", "close"):
        pn2[name].loc[mask] = pn2[name].loc[mask] * 7.0 + 5.0
    for name in ("volume", "quote_volume"):
        pn2[name].loc[mask] = pn2[name].loc[mask] * 3.0 + 1.0

    aux2 = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in aux.items()}
    emask = aux2["eligibility"].index > cut
    aux2["eligibility"].loc[emask] = ~aux2["eligibility"].loc[emask]

    corrupted = strategy.build_raw_weights(pn2, aux2)

    a = full.loc[full.index <= cut]
    b = corrupted.loc[corrupted.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_same_bar_perturbation_before_t_unchanged():
    """Perturb close at candle t* only; weights STRICTLY BEFORE t* are unchanged."""
    pn, aux = _make_panels()
    full = strategy.build_raw_weights(pn, aux)

    pos = 200
    t_star = pn["close"].index[pos]
    pn2 = {k: v.copy() for k, v in pn.items()}
    pn2["close"].loc[t_star] = pn2["close"].loc[t_star] * 1.001
    perturbed = strategy.build_raw_weights(pn2, aux)

    a = full.loc[full.index < t_star]
    b = perturbed.loc[perturbed.index < t_star]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_widening_extra_never_eligible_columns():
    """Extra synthetic never-eligible columns must not crash the strategy (widening realism)."""
    pn, aux = _make_panels()
    idx = pn["close"].index
    extra = [f"ZZWIDE{i:02d}USDT" for i in range(3)]
    rng = np.random.default_rng(7)

    pn2 = {k: v.copy() for k, v in pn.items()}
    for name, frame in pn2.items():
        add = pd.DataFrame(
            rng.uniform(1.0, 100.0, size=(len(idx), len(extra))), index=idx, columns=extra
        )
        pn2[name] = pd.concat([frame, add], axis=1)

    elig2 = aux["eligibility"].copy()
    for c in extra:
        elig2[c] = False
    aux2 = {"eligibility": elig2, "seed": aux["seed"]}

    w = strategy.build_raw_weights(pn2, aux2)
    assert isinstance(w, pd.DataFrame)
    assert all(c in w.columns for c in extra)
    assert (w[extra] == 0.0).to_numpy().all()  # never-eligible columns stay flat


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"ok {_name}")
    print("all tests passed")
