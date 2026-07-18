"""team-04 strategy self-checks — the SPEC-required leak-proofing tests (research_brief.md
section 8). Run with:  uv run pytest tournament/crypto/teams/team-04/test_strategy.py -q

Constraints honored so the static import/path scan stays clean (it scans this file too):
imports are numpy / pandas / the team-local ``strategy`` module ONLY. No pytest import (plain
asserts; pytest still collects ``test_*`` functions), no importlib / pathlib, no file reads,
no prohibited path literals. All panels are built in-memory and deterministically.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

_STEP_MS = 8 * 60 * 60 * 1000  # 8h grid


def _make_close(n_rows: int = 640, n_syms: int = 6, seed: int = 7) -> pd.DataFrame:
    """A deterministic 8h close panel (geometric random walks), DatetimeIndex x symbols.

    A couple of names list mid-panel (leading NaN) so the young-listing / NaN-skipping-blend
    paths are exercised — mirroring the real IS panel where coins enter the top-40 late.
    """
    rng = np.random.default_rng(seed)
    idx = pd.to_datetime(
        np.arange(n_rows, dtype=np.int64) * _STEP_MS + 1_577_836_800_000, unit="ms"
    )
    cols = [f"SYM{i:02d}USDT" for i in range(n_syms)]
    data = {}
    for j, c in enumerate(cols):
        px = 100.0 * np.exp(np.cumsum(rng.normal(0.0002 * (j - 2), 0.02, size=n_rows)))
        s = pd.Series(px, index=idx)
        if j >= n_syms - 2:  # last two names list mid-panel
            s.iloc[: 150 + 40 * (j - (n_syms - 2))] = np.nan
        data[c] = s
    return pd.DataFrame(data, index=idx)


def _aux() -> dict:
    # aux must be accepted; the strategy must not read it. Populate it with a seed and a
    # decoy panel to prove indifference.
    return {"seed": 12345, "funding": pd.DataFrame()}


def _weights(close: pd.DataFrame) -> pd.DataFrame:
    return strategy.build_raw_weights({"close": close}, _aux())


# ---------------------------------------------------------------- (a) future corruption --------
def test_future_corruption_leaves_past_bit_identical():
    """Corrupt close[t+k], k>=1; weights AT and BEFORE t must be bit-unchanged."""
    close = _make_close()
    t_pos = 420
    t = close.index[t_pos]
    w_full = _weights(close)

    corrupt = close.copy()
    # mangle every row strictly after t (positive-preserving, like the harness).
    corrupt.iloc[t_pos + 1 :] = corrupt.iloc[t_pos + 1 :] * 7.0 + 5.0
    w_corrupt = _weights(corrupt)

    a = w_full[w_full.index <= t]
    b = w_corrupt[w_corrupt.index <= t]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


# ---------------------------------------------------------------- (b) widening -----------------
def test_widening_extra_columns_do_not_change_existing():
    """Append a synthetic all-NaN column and a synthetic constant-price column; no crash,
    existing columns' weights bit-unchanged, and the two synthetic names stay flat (NaN)."""
    close = _make_close()
    w_base = _weights(close)

    wide = close.copy()
    wide["ZZNANUSDT"] = np.nan
    wide["ZZFLATUSDT"] = 100.0  # constant price -> zero vol -> flat everywhere
    w_wide = _weights(wide)

    assert isinstance(w_wide, pd.DataFrame)
    pd.testing.assert_frame_equal(
        w_wide[close.columns], w_base, check_exact=True, check_like=False
    )
    assert w_wide["ZZNANUSDT"].isna().all()
    assert w_wide["ZZFLATUSDT"].isna().all()


# ---------------------------------------------------------------- (c) determinism --------------
def test_determinism_two_calls_bit_equal():
    """Two calls on independent copies must be bit-identical (no unseeded state)."""
    close = _make_close()
    w1 = strategy.build_raw_weights({"close": close.copy()}, _aux())
    w2 = strategy.build_raw_weights({"close": close.copy()}, _aux())
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


# ---------------------------------------------------------------- (d) NaN tolerance ------------
def test_nan_tolerance_interior_run():
    """An interior NaN run in one column must not raise, must leave those cells flat (NaN),
    and must not change any OTHER column (per-name independence)."""
    close = _make_close()
    w_base = _weights(close)

    injected = close.copy()
    col = injected.columns[0]
    lo, hi = 300, 320
    injected.iloc[lo:hi, injected.columns.get_loc(col)] = np.nan
    w_nan = _weights(injected)  # must not raise

    # injected cells are flat
    assert w_nan[col].iloc[lo:hi].isna().all()
    # every other column is bit-unchanged
    others = [c for c in close.columns if c != col]
    pd.testing.assert_frame_equal(w_nan[others], w_base[others], check_exact=True)


# ---------------------------------------------------------------- (e) same-bar honesty ---------
def test_same_bar_close_moves_weight_at_t():
    """Weights at t MUST change when close[t] changes (same-bar convention the engine lags by
    one candle); weights STRICTLY BEFORE t must stay bit-unchanged."""
    close = _make_close()
    t_pos = 420
    t = close.index[t_pos]
    w_full = _weights(close)

    pert = close.copy()
    pert.iloc[t_pos] = pert.iloc[t_pos] * 1.001
    w_pert = _weights(pert)

    # rows strictly before t unchanged
    before_a = w_full[w_full.index < t]
    before_b = w_pert[w_pert.index < t]
    pd.testing.assert_frame_equal(before_a, before_b, check_exact=True)

    # row t is non-NaN somewhere and actually changed
    row_full = w_full.loc[[t]]
    row_pert = w_pert.loc[[t]]
    assert not row_full.isna().all(axis=1).iloc[0]
    assert not row_full.equals(row_pert)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all self-checks passed")
