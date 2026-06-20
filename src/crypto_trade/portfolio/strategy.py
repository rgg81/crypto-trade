"""Shared weight engine for the live portfolio — PARITY BY CONSTRUCTION.

The live executor and the backtest compute target weights from the SAME code. This module imports
the validated backtest modules (analysis/portfolio/iter_002,004,005,020) and exposes:
- position_weight_book(coins) -> DataFrame : full per-candle DEPLOYED position weights (banded,
  gross-renormed, vol-targeted) == iter_020 baseline-v2.
- next_target_weights(coins) -> dict : position weights to HOLD for the UPCOMING candle, decided at
  the latest candle close (un-lagged signal).

Deployed config (baseline-v2): trend+carry (walk-forward lambda), inverse-vol sized,
gross-normalized L/S, vol-targeted (1%/candle, max 3x), hysteresis SNAP delta 0.010.

The iter_* modules use CWD-relative data paths + bare sibling imports, so we put analysis/portfolio
on the path and run data ops with CWD = repo root.
"""

from __future__ import annotations

import contextlib
import os
import sys

import numpy as np
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_AP = os.path.join(_ROOT, "analysis", "portfolio")
if _AP not in sys.path:
    sys.path.insert(0, _AP)

import iter_002_top20 as _base  # noqa: E402
import iter_020_hysteresis as _hy  # noqa: E402

DELTA = 0.010   # baseline-v2 hysteresis band (SNAP)
MODE = "snap"


@contextlib.contextmanager
def _in_root():
    """Run the iter_* data ops with CWD = repo root so their relative data paths resolve."""
    cwd = os.getcwd()
    os.chdir(_ROOT)
    try:
        yield
    finally:
        os.chdir(cwd)


def candidate_symbols() -> list[str]:
    """Candidate-universe symbols (ex-stable, ascii) WITHOUT loading every CSV — for kline refresh.

    Mirrors iter_002.load_universe's symbol filter (the >=2y-history cut is applied later by
    load_universe). Used to know which symbols' klines+funding the live tick must keep fresh, so the
    PIT top-20 selection matches the backtest (which scans the full candidate set).
    """
    import glob
    import os.path

    syms = []
    for p in sorted(glob.glob(os.path.join(_ROOT, "data", "*USDT", "8h.csv"))):
        sym = os.path.basename(os.path.dirname(p))
        if not sym.endswith("USDT") or _base.STABLE.search(sym) or not sym.isascii():
            continue
        syms.append(sym)
    return syms


def load_universe() -> dict:
    """PIT candidate universe (data/<SYM>/8h.csv, ex-stable, >=2y history). CWD-independent."""
    with _in_root():
        return _base.load_universe()


def _deployed_weights(book: dict, delta: float, mode: str) -> pd.DataFrame:
    """Deployed position weights = banded held -> renorm to baseline gross -> x vol-target scale.

    Identical construction to iter_020.banded_net (which books P&L from exactly this `w * scale`).
    """
    target_w = book["target_w"]
    held = _hy.apply_band(target_w, delta, mode)
    base_gross = target_w.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    w = held.mul((base_gross / held_gross).fillna(0.0), axis=0)          # banded, renormed
    return w.mul(book["scale"], axis=0)                                  # x per-candle vol-target


def position_weight_book(coins: dict, delta: float = DELTA, mode: str = MODE) -> pd.DataFrame:
    """Full per-candle deployed position-weight matrix (rows = candle datetimes, cols = coins).

    Row t is the weight HELD during candle t (decided at close[t-1]) — the backtest's traded book.
    """
    book = _hy.canonical_book(coins, _hy.build_books(coins))
    return _deployed_weights(book, delta, mode)


def next_target_weights(coins: dict, delta: float = DELTA, mode: str = MODE) -> dict:
    """Position weights to HOLD for the UPCOMING candle, decided at the latest candle close.

    The backtest lags weights by one candle (`w = raw.shift(1)`), so the live "next" weight is the
    un-lagged signal at the latest close. We band it against the latest deployed held weights and
    apply the latest vol-target scale — the row the backtest WOULD place at the next candle.

    Returns {symbol: signed_weight} for non-trivial targets, plus metadata under "_meta".
    """
    book = _hy.canonical_book(coins, _hy.build_books(coins))
    target_w = book["target_w"]                  # lagged target weights (held during each candle)
    held = _hy.apply_band(target_w, delta, mode)  # the backtest's banded held chain
    raw_next = target_w.shift(-1).iloc[-1]            # raw[T] = next-candle target (un-lagged)
    held_last = held.iloc[-1]
    move = raw_next - held_last
    nxt = held_last.copy()
    if delta > 0:
        trig = move.abs() > delta
        if mode == "edge":
            nxt[trig] = held_last[trig] + np.sign(move[trig]) * (move[trig].abs() - delta)
        else:
            nxt[trig] = raw_next[trig]
    else:
        nxt = raw_next.copy()
    gross = nxt.abs().sum()
    base_gross = float(target_w.iloc[-1].abs().sum())
    if gross > 0:
        nxt = nxt * (base_gross / gross)
    scale = float(book["scale"].iloc[-1])
    pos = (nxt * scale).dropna()
    out = {s: float(v) for s, v in pos.items() if abs(v) > 1e-9}
    out["_meta"] = {
        "as_of": str(target_w.index[-1]),
        "lambda_pick": book["picks"][-1] if book["picks"] else None,
        "vol_target_scale": scale,
        "gross": float(pos.abs().sum()),
        "n_positions": int((pos.abs() > 1e-9).sum()),
    }
    return out
