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


def append_forming(coins: dict, forming_opens: dict) -> dict:
    """Append the just-opened (forming) candle's OPEN per coin so the deployed book covers the HOLD
    candle. Bit-exact parity needs open[H] (the vol-target scale[H] uses it); close[H]/qv[H] do NOT
    affect deployed[H], so we placeholder them. forming_opens = {sym: (open_time_ms, open_px)}.
    """
    out = {}
    for s, d in coins.items():
        fo = forming_opens.get(s)
        if fo is None:
            out[s] = d
            continue
        ot, px = int(fo[0]), float(fo[1])
        if len(d) and ot <= int(d.index[-1]):
            out[s] = d                      # forming candle already closed/in data
            continue
        last_qv = float(d["quote_volume"].iloc[-1]) if len(d) else 0.0
        row = pd.DataFrame({"open": [px], "close": [px], "quote_volume": [last_qv]}, index=[ot])
        out[s] = pd.concat([d, row])
    return out


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
    """Deployed position weights to HOLD during the LATEST candle in `coins` — the live target.

    BIT-EXACT DEFINITION (verified by reconcile_live): the deployed weight for the candle being held
    = the LAST ROW of the full deployed book (banded -> renorm -> x vol-target). The vol scale
    for candle H depends on open[H] (via raw_net[H-1] = w[H-1]*(open[H]/open[H-1]-1)), so the CALLER
    must feed `coins` ending at the HOLD candle — i.e. include the just-opened candle's open. Live:
    when candle H-1 closes, candle H has opened; fetch through H's open, compute, rebalance.

    Because the book is recomputed from FULL history, the month's walk-forward lambda and the
    path-dependent band chain are reproduced from data — so a mid-month start is handled
    automatically. Returns {symbol: signed_weight} for non-trivial holds, plus "_meta".
    """
    book = _hy.canonical_book(coins, _hy.build_books(coins))
    deployed = _deployed_weights(book, delta, mode)        # full per-candle deployed book
    last = deployed.iloc[-1]                                # weight held during the latest candle
    pos = last[last.abs() > 1e-9]
    out = {s: float(v) for s, v in pos.items()}
    out["_meta"] = {
        "as_of": str(deployed.index[-1]),
        "lambda_pick": book["picks"][-1] if book["picks"] else None,
        "gross": float(last.abs().sum()),
        "n_positions": int(len(pos)),
    }
    return out
