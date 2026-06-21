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
import iter_021_eligexit as _ee  # noqa: E402

DELTA = 0.010   # baseline-v3 hysteresis band (SNAP)
MODE = "snap"
K_EXIT = 2      # baseline-v3 eligibility-exit: force-close after K candles out of top-20


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


def forming_from_close(coins: dict) -> dict:
    """Build the forming (hold) candle's open per ACTIVE coin from its last close — non-ragged.

    The next candle's open ~= the prior close (measured gap < 0.01%), so close[last] is a near-exact
    proxy for open[H]. Using it for EVERY active coin (last candle == the global latest) avoids the
    ragged-panel bug a partial fetch caused, with relative weights BIT-EXACT and the vol-target
    gross scalar off by < 0.1%. Returns {sym: (next_open_time_ms, close[last])}. 8h candle assumed.
    """
    if not coins:
        return {}
    step = 8 * 60 * 60 * 1000
    global_last = max(int(d.index[-1]) for d in coins.values() if len(d))
    out = {}
    for s, d in coins.items():
        if len(d) and int(d.index[-1]) == global_last:
            out[s] = (global_last + step, float(d["close"].iloc[-1]))
    return out


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


def _deployed_weights(book: dict, coins: dict, delta: float, mode: str,
                      k_exit: float = K_EXIT) -> pd.DataFrame:
    """Deployed position weights = band + ELIGIBILITY-EXIT held -> renorm -> x vol-target scale.

    baseline-v3: iter_020's no-trade band PLUS iter_021's eligibility-exit (force-close coins out of
    the top-20 for >= k_exit candles, clearing the zombie/delisted tail). k_exit=inf reproduces v2.
    Books P&L from exactly this `w * scale` (mirrors iter_021.eligexit_net).
    """
    target_w = book["target_w"]
    elig = _ee.eligibility_mask(coins, target_w)
    held = _ee.apply_band_eligexit(target_w, elig, delta, k_exit, mode)
    base_gross = target_w.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    w = held.mul((base_gross / held_gross).fillna(0.0), axis=0)          # banded+exited, renormed
    return w.mul(book["scale"], axis=0)                                  # x per-candle vol-target


def position_weight_book(coins: dict, delta: float = DELTA, mode: str = MODE) -> pd.DataFrame:
    """Full per-candle deployed position-weight matrix (rows = candle datetimes, cols = coins).

    Row t is the weight HELD during candle t (decided at close[t-1]) — the backtest's traded book.
    """
    book = _hy.canonical_book(coins, _hy.build_books(coins))
    return _deployed_weights(book, coins, delta, mode)


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
    deployed = _deployed_weights(book, coins, delta, mode)  # full per-candle deployed book
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
