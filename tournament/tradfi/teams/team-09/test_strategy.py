"""team-09 team-owned tests for t09-jump-momentum-v1 strategy.py.

Imports are restricted to the audit static-scan whitelist: numpy, pandas, and the local
`strategy` module ONLY (no pytest import — pytest collects bare ``test_*`` functions that use
plain ``assert``). Data is synthetic and generated deterministically here; no file I/O.

Covers (at minimum, per the QE mandate):
- a strategy-specific FUTURE-CORRUPTION self-check (mangle bars strictly after a cut; assert
  weights at/before the cut are byte-identical), and
- a DETERMINISM test (two fresh calls on identical inputs emit identical weights).
Plus past-only warmup, output-grid, market-neutral-tilt, and aux-ignored sanity checks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

_L = 42  # trailing window (matches the frozen spec; first L-1 rows must be flat)


def _make_panel(n_rows: int = 420, n_cols: int = 30, seed: int = 7) -> dict[str, pd.DataFrame]:
    """A synthetic OHLCV-style panel dict with ragged starts (point-in-time NaN prefixes).

    Only ``close`` is consumed by the strategy; the other panels are supplied to mirror the
    real interface. Close paths are strictly positive random walks so returns stay finite.
    """
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n_rows)
    cols = [f"AAA{j:02d}USDT" for j in range(n_cols)]
    steps = rng.normal(loc=0.0005, scale=0.02, size=(n_rows, n_cols))
    close = 100.0 * np.exp(np.cumsum(steps, axis=0))
    df = pd.DataFrame(close, index=idx, columns=cols)
    # ragged starts: column j is unavailable for its first 3*j rows (never forward-filled)
    for j, col in enumerate(cols):
        if j > 0:
            df.iloc[: 3 * j, j] = np.nan
    return {k: df.copy() for k in ("open", "high", "low", "close", "volume")}


def _aux(seed: int = 20260717) -> dict:
    return {"vix": None, "sector_map": {}, "seed": seed}


def test_determinism():
    """Two fresh calls on identical inputs must emit bit-identical weights."""
    pn = _make_panel()
    w1 = strategy.build_raw_weights(pn, _aux())
    w2 = strategy.build_raw_weights(_make_panel(), _aux())  # rebuilt-from-scratch inputs
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_future_corruption_leaves_past_unchanged():
    """Mangle every bar STRICTLY AFTER a cut (close * 7 + 5). Weights at/before the cut must
    be byte-identical — the strategy is past-only (no future read can leak backward)."""
    pn = _make_panel()
    w_full = strategy.build_raw_weights(pn, _aux())

    cut = 300  # well past the L-1 warmup and the ragged-start region
    assert cut < len(pn["close"]) - 1
    corrupted = {k: df.copy() for k, df in pn.items()}
    close_c = corrupted["close"].copy()
    close_c.iloc[cut + 1 :, :] = close_c.iloc[cut + 1 :, :] * 7.0 + 5.0
    corrupted["close"] = close_c
    # mangle the other panels too, matching the harness spirit (strategy ignores them anyway)
    for k in ("open", "high", "low"):
        corrupted[k].iloc[cut + 1 :, :] = corrupted[k].iloc[cut + 1 :, :] * 7.0 + 5.0
    corrupted["volume"].iloc[cut + 1 :, :] = corrupted["volume"].iloc[cut + 1 :, :] * 3.0 + 1.0

    w_corrupt = strategy.build_raw_weights(corrupted, _aux())
    pd.testing.assert_frame_equal(
        w_full.iloc[: cut + 1], w_corrupt.iloc[: cut + 1], check_exact=True
    )


def test_same_bar_perturbation_leaves_strict_past_unchanged():
    """Perturb close[t*] only; weights STRICTLY BEFORE t* must be unchanged (close[t*] is
    legitimately available to the t* decision, but never to earlier ones)."""
    pn = _make_panel()
    w_full = strategy.build_raw_weights(pn, _aux())
    t_star = 280
    perturbed = {k: df.copy() for k, df in pn.items()}
    cl = perturbed["close"].copy()
    cl.iloc[t_star, :] = cl.iloc[t_star, :] * 1.001
    perturbed["close"] = cl
    w_p = strategy.build_raw_weights(perturbed, _aux())
    pd.testing.assert_frame_equal(w_full.iloc[:t_star], w_p.iloc[:t_star], check_exact=True)


def test_warmup_rows_are_flat():
    """The first L-1 rows have an incomplete trailing window -> JUMP NaN -> flat (all zero),
    and the causal EMA of leading zeros stays exactly zero."""
    pn = _make_panel()
    w = strategy.build_raw_weights(pn, _aux())
    warm = w.iloc[: _L - 1]
    assert (warm.to_numpy() == 0.0).all()


def test_output_grid_matches_close():
    """Output is aligned to the close panel's index and columns exactly."""
    pn = _make_panel()
    w = strategy.build_raw_weights(pn, _aux())
    assert list(w.index) == list(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)


def test_active_rows_are_market_neutral_tilt():
    """On active rows the centered rank sums to ~0 cross-sectionally (dollar-neutral raw book,
    pre-engine). The EMA of neutral rows stays neutral."""
    pn = _make_panel()
    w = strategy.build_raw_weights(pn, _aux())
    active = w.abs().sum(axis=1) > 0
    assert active.any()
    row_sums = w[active].sum(axis=1).abs()
    assert (row_sums < 1e-9).all()


def test_long_high_jump_direction():
    """Family fidelity: the name that consistently owns the top of the jump cross-section gets
    a POSITIVE raw weight (long high-jump), the boring end negative. Column 5 is given large
    positive daily jumps recurring through the trailing window so it stays the top-JUMP name;
    the causal EMA therefore accumulates a positive, cross-sectionally maximal weight."""
    idx = pd.bdate_range("2015-01-01", periods=200)
    cols = [f"N{j:02d}" for j in range(20)]
    rng = np.random.default_rng(1)
    rets = rng.normal(0.0, 0.001, size=(200, 20))
    # column 5: a big +8% jump every 5th day across the last 60 rows -> its top-3 daily returns
    # dominate every trailing-42 window in that region, so it owns the cross-section top.
    rets[140:, 5] = 0.0
    rets[140:200:5, 5] = 0.08
    close = pd.DataFrame(100.0 * np.cumprod(1.0 + rets, axis=0), index=idx, columns=cols)
    pn = {k: close.copy() for k in ("open", "high", "low", "close", "volume")}
    w = strategy.build_raw_weights(pn, _aux())
    last = w.iloc[-1]
    assert last["N05"] == last.max()
    assert last["N05"] > 0.0


def test_aux_is_ignored():
    """The strategy reads no aux field: two different aux dicts yield identical weights."""
    pn = _make_panel()
    w_a = strategy.build_raw_weights(pn, {"vix": None, "sector_map": {}, "seed": 1})
    fake_vix = pd.Series(20.0, index=pn["close"].index)
    w_b = strategy.build_raw_weights(
        pn, {"vix": fake_vix, "sector_map": {c: "X" for c in pn["close"].columns}, "seed": 999}
    )
    pd.testing.assert_frame_equal(w_a, w_b, check_exact=True)
