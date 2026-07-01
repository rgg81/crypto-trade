"""Paper-desk funding accounting — REAL Binance 4h funding folded into the metals paper PnL.

PAPER-ONLY realism (user 2026-07-01: "account those trades in a realistic manner"). Funding is a
POST-DECISION PnL adjustment on the DEPLOYED (levered) positions — it NEVER touches the strategy
signals, so the held book is bit-for-bit identical with/without funding and backtest↔live parity is
preserved. The strategy's Sharpe is unchanged; only the live PAPER equity gains the funding leg.

CAUSAL / NO LOOK-AHEAD. Binance metal perps fund every 4h (00/04/08/12/16/20 UTC) — two settlements
per 8h candle. Candle t is charged the settlements whose fundingTime FLOORS to t on the 8h grid,
i.e. {t, t+4h} (the t+8h settlement floors to the NEXT candle). The load-bearing guarantee is the
engine's COMPLETE-CANDLE GATE: it only ever loads candles with ``open_time + 8h <= now``
(``live_metals._refresh_one``), so for EVERY booked candle t both {t, t+4h} are already settled — no
rate is ever used ahead of its fundingTime. (Binance stamps fundingTime as the grid instant +1ms;
integer-floor is unaffected. Funding rides the same ``price_net.index`` support as the cost leg, so
the two stay in lockstep.)

SIGN. fundingRate > 0 => longs pay shorts. A signed position w is charged w*rate (a long pays when
rate>0), so per-candle funding PnL = -sum_i deployed[t,i] * (sum of 4h rates flooring to t).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

STEP_MS = 8 * 60 * 60 * 1000  # 8h candle, in ms


def load_funding(funding_dir: str | Path, symbols) -> dict[str, pd.Series]:
    """Load per-symbol funding series (index = fundingTime ms, value = fundingRate).

    Reads the same ``<dir>/funding_rates/<SYM>.csv`` schema written by
    ``crypto_trade.portfolio.funding.refresh_funding`` (columns: funding_time, funding_rate).
    A missing file yields an empty series (that symbol contributes zero funding).
    """
    out: dict[str, pd.Series] = {}
    d = Path(funding_dir) / "funding_rates"
    for s in symbols:
        p = d / f"{s}.csv"
        if p.exists():
            df = pd.read_csv(p)
            out[s] = df.set_index("funding_time")["funding_rate"].sort_index()
        else:
            out[s] = pd.Series(dtype=float)
    return out


def funding_net_8h(deployed: pd.DataFrame, funding: dict[str, pd.Series]) -> pd.Series:
    """Per-8h-candle funding PnL fraction on the DEPLOYED book (causal; see module docstring).

    ``deployed``: index = candle open_time (8h grid; datetime64 OR int ms); columns = symbols;
    values = weights. Returns a Series (candle open_time -> funding_net fraction) aligned to
    ``deployed.index``. A candle with no funding settlement (pre-listing history) contributes 0.

    Alignment is done positionally in integer-ms so a datetime64 vs int-ms index mismatch can never
    silently zero the funding out.
    """
    idx = deployed.index
    if pd.api.types.is_datetime64_any_dtype(idx):
        idx_ms = pd.DatetimeIndex(idx).astype("datetime64[ms]").astype("int64").to_numpy()
    else:
        idx_ms = np.asarray(idx, dtype="int64")
    fn = pd.Series(0.0, index=idx)
    for s in deployed.columns:
        fr = funding.get(s)
        if fr is None or not len(fr):
            continue
        # Floor each 4h fundingTime to the 8h candle open it belongs to, then sum the (<=2) 4h
        # rates per candle. Settlement at t+8h floors to the NEXT candle, so no double-counting.
        candle = (fr.index.to_numpy() // STEP_MS) * STEP_MS
        per_candle = fr.groupby(candle).sum()
        rate = per_candle.reindex(idx_ms).fillna(0.0).to_numpy()  # positional, per deployed candle
        fn = fn - deployed[s].to_numpy() * rate
    return fn
